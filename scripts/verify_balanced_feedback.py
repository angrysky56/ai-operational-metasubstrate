"""Verify all 96 saved actor calls and complete review coverage without inference."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from statistics import fmean, median

from analyze_challenge_test import flags
from feedback_harness import CAPABILITY, read_ends, score, sha
from jev_review_records import complete_reviews
from run_locked_ollama import messages_for, response_status
from run_ollama import stamp
from visible_plan_validator import gate, review_fields, validate

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> dict:
    """Load exact saved JSON."""
    return json.loads(path.read_text())


def verify(out: Path) -> dict:
    """Recompute inputs, pairings, keyed scores and every final gate decision."""
    lock = read(out / "precollection-lock.json")
    correction_lock = read(out / "correction-input-lock.json")
    source = read(out / "initial-dataset.json")
    correction = read(out / "correction-dataset.json")
    analysis = read(out / "balanced-analysis.json")
    checks = {}
    for name, expected in lock["source_hashes"].items():
        checks["live_source:" + name] = sha(ROOT / name) == expected
        checks["frozen_source:" + name] = sha(out / ("frozen-" + Path(name).name)) == expected
    checks["correction_inputs_frozen"] = (sha(out / "correction-dataset.json") == correction_lock["dataset_sha256"]
        and sha(out / "initial/events.jsonl") == correction_lock["initial_events_sha256"]
        and sha(out / "precollection-lock.json") == correction_lock["precollection_lock_sha256"]
        and sha(out / "initial-reviews.json") == correction_lock["initial_reviews_sha256"])
    ends, backends, configs = {}, set(), {}
    for stage, data, seed in (("initial", source, 20261013), ("corrections", correction, 20261014)):
        directory = out / stage
        manifest = read(directory / "manifest.json")
        config = manifest["config"]
        configs[stage] = config
        backends.add(json.dumps(config["backend"], sort_keys=True))
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
        starts = [e for e in events if e["event"] == "started"]
        terminal = [e for e in events if e["event"] == "finished"]
        ends[stage] = read_ends(directory)
        planned = {cell["id"]: cell for cell in manifest["order"]}
        checks[stage + ":unique_complete_accounting"] = (len(starts) == len(terminal) == len(ends[stage]) == len(planned) == 48
            and {e["cell"] for e in starts} == set(planned) == set(ends[stage])
            and {e["attempt"] for e in starts} == {e["attempt"] for e in terminal})
        checks[stage + ":locked_generator"] = config["model"] == lock["settings"]["model"] and config["digest"] == lock["settings"]["digest"] and config["options"] == lock["settings"]["options"] and config["think"] is True and config["stream"] is True and config["order_seed"] == seed and config["max_attempts"] == 48 and config["request_timeout"] == 900
        checks[stage + ":exact_visible_requests"] = all(e["request"]["messages"] == messages_for(data, planned[e["cell"]]) and e["request"]["options"] == lock["settings"]["options"] and e["request"]["stream"] is True and e["request"]["think"] is True for e in starts)
        checks[stage + ":dataset_snapshot"] = sha(directory / "dataset.json") == config["dataset_sha256"] == sha(out / ("initial-dataset.json" if stage == "initial" else "correction-dataset.json"))
        checks[stage + ":status_from_actual_response"] = all(e["status"] == response_status(e["raw"]) for e in terminal if e["status"] != "error")
    checks["same_backend"] = len(backends) == 1
    initial_seconds = sum(e["elapsed_seconds"] for e in ends["initial"].values())
    total_seconds = initial_seconds + sum(e["elapsed_seconds"] for e in ends["corrections"].values())
    checks["actor_budget"] = initial_seconds <= 7200 and total_seconds <= 14400 and configs["initial"]["max_seconds"] == 7200 and configs["corrections"]["max_seconds"] == 14400 - math.ceil(initial_seconds)
    original = read(ROOT / "data/challenge-test-v1.json")
    checks["all_original_cases_preserved"] = source["cases"] == original["cases"] and len(source["cases"]) == 24 and set(source["conditions"]) == {"P1", "P2"}
    for c in correction["cases"]:
        case = next(x for x in source["cases"] if x["id"] == c["origin_case"])
        condition = c["actor_condition"]
        initial = ends["initial"][case["id"] + "-" + condition]
        expected_history = case.get("history", []) + [{"role": "user", "content": case["prompt"]}, {"role": "assistant", "content": initial["raw"].get("message", {}).get("content", "")}]
        checks[c["id"] + ":own_condition_history"] = c["conditions"] == [condition] and c["history"] == expected_history
    recovered = {}
    all_traces = []
    for stage in ("initial", "final"):
        binding_file = read(out / (stage + "-review-bindings.json"))
        bindings, validations = binding_file["bindings"], binding_file["validations"]
        full = {case["id"] + "-" + condition: [] for case in source["cases"] for condition in ("P1", "P2")}
        used_ids = []
        for path in sorted(out.glob(stage + "-batch-*-request.json")):
            if "trace-request" in path.name:
                continue
            request = read(path)
            prefix = path.name.removesuffix("-request.json")
            result = read(out / (prefix + "-result.json"))["structuredContent"]["result"]
            trace = read(out / (prefix + "-trace.json"))["structuredContent"]["result"]
            items = request["items"]
            checks[prefix + ":identity_and_budget"] = result["capability"] == CAPABILITY and result["runId"] == trace["runId"] and len(items) <= 12 and request["maxCalls"] == len(items) and request["context"] == {} and request["useCache"] is False
            rows = complete_reviews(trace, items, {item["id"]: bindings[item["id"]] for item in items}, CAPABILITY)
            for pair, reviews in rows.items():
                full[pair].extend(reviews)
            used_ids.extend(item["id"] for item in items)
            all_traces.append(trace)
        checks[stage + ":every_requested_item_once"] = len(used_ids) == len(set(used_ids)) == len(bindings) and set(used_ids) == set(bindings)
        checks[stage + ":stored_reviews_exact"] = full == read(out / (stage + "-reviews.json"))["by_pair"]
        for case in source["cases"]:
            for condition in ("P1", "P2"):
                pair = case["id"] + "-" + condition
                cell = pair if stage == "initial" else pair + "-feedback-" + condition
                event = ends["initial" if stage == "initial" else "corrections"][cell]
                current = validate(case["family"], case["prompt"], event["raw"].get("message", {}).get("content", ""), event["status"] == "complete")
                selected = review_fields(current)
                checks[stage + ":exact_visible_validation:" + pair] = validations[pair] == current
                actual_items = {item["id"]: item["data"] for path in sorted(out.glob(stage + "-batch-*-request.json")) if "trace-request" not in path.name for item in read(path)["items"]}
                actual = [actual_items[item_id] for item_id, binding in bindings.items() if binding["case_id"] == pair]
                checks[stage + ":selected_fields_only:" + pair] = actual == selected and all(set(item) == {"field_path", "field_value", "reason"} for item in actual)
        recovered[stage] = full
    checks["reviewer_budget"] = sum(t["summary"]["modelCalls"] for t in all_traces) <= 192 and all(t["summary"]["cacheHits"] == 0 for t in all_traces)
    safety_rows = []
    for row in analysis["rows"]:
        case = next(c for c in source["cases"] if c["id"] == row["case_id"])
        pair = case["id"] + "-" + row["condition"]
        initial, final = ends["initial"][pair], ends["corrections"][pair + "-feedback-" + row["condition"]]
        initial_score, final_score = score(initial, case["checks"]), score(final, case["checks"])
        checks[pair + ":keyed_scores_recompute"] = row["initial_success"] == initial_score["success"] and row["final_success"] == final_score["success"] and row["payload"] == final_score.get("payload")
        checks[pair + ":status_and_review_rows"] = (row["family"] == case["family"]
            and row["initial_status"] == initial["status"] and row["final_status"] == final["status"]
            and row["pre_output_pass"] == final["raw"].get("pre_output_audit", {}).get("pass", False)
            and all(row[phase + "_reviews"] == recovered[phase][pair]
                and row[phase + "_contradiction"] == any(r.get("choice") == "contradicts_payload" and r.get("confidence", 0) >= 0.8 for r in recovered[phase][pair])
                for phase in ("initial", "final")))
        validation = validate(case["family"], case["prompt"], final["raw"].get("message", {}).get("content", ""), final["status"] == "complete")
        reason = (validation["payload"] or {}).get("reason")
        present = isinstance(reason, str) and bool(reason.strip())
        decision = gate(validation, recovered["final"][pair], require_reviews=True) if present else {"accepted": False, "reason": "missing_required_reason"}
        checks[pair + ":exact_final_gate"] = row["gate"] == decision and row["reason_present"] == present and row["runtime_valid"] == validation["valid"]
        safety_rows.append({"case_id": case["id"], "condition": row["condition"], "status": final["status"], "flags": flags(final_score.get("payload"), case)})
    checks["forty_eight_unique_scored_pairs"] = len(analysis["rows"]) == len({(r["case_id"], r["condition"]) for r in analysis["rows"]}) == 48
    families, resources = {}, {}
    for condition in ("P1", "P2"):
        selected = [r for r in analysis["rows"] if r["condition"] == condition]
        transition = Counter((bool(r["initial_success"]), bool(r["final_success"])) for r in selected)
        expected = {"planned": len(selected), "initial_success": transition[True, False] + transition[True, True],
            "final_success": transition[False, True] + transition[True, True], "repairs": transition[False, True],
            "regressions": transition[True, False], "accepted": sum(r["gate"]["accepted"] for r in selected),
            "wrong_accepted": sum(r["gate"]["accepted"] and not r["final_success"] for r in selected),
            "correct_withheld": sum(not r["gate"]["accepted"] and r["final_success"] for r in selected),
            "initial_contradictions": sum(r["initial_contradiction"] for r in selected),
            "final_contradictions": sum(r["final_contradiction"] for r in selected),
            "incomplete_initial": sum(r["initial_status"] != "complete" for r in selected),
            "incomplete_final": sum(r["final_status"] != "complete" for r in selected)}
        checks[condition + ":aggregate_totals"] = analysis["totals"][condition] == expected
        for family in sorted({r["family"] for r in selected}):
            subset = [r for r in selected if r["family"] == family]
            families.setdefault(family, {})[condition] = {"planned": len(subset),
                "initial_success": sum(r["initial_success"] for r in subset),
                "final_success": sum(r["final_success"] for r in subset)}
    paired = Counter()
    for case in source["cases"]:
        correct = {r["condition"] for r in analysis["rows"] if r["case_id"] == case["id"] and r["final_success"]}
        paired["both_pass" if len(correct) == 2 else "P1_only" if correct == {"P1"} else "P2_only" if correct else "both_fail"] += 1
    checks["paired_counts_and_difference"] = (analysis["paired_final"] == {name: paired[name] for name in ("both_pass", "P1_only", "P2_only", "both_fail")}
        and analysis["P2_minus_P1_pp"] == 100 * (paired["P2_only"] - paired["P1_only"]) / 24)
    for stage, events in ends.items():
        usage = {"calls": len(events), "request_seconds": sum(e["elapsed_seconds"] for e in events.values()),
            "input_tokens": sum(e["raw"].get("prompt_eval_count", 0) for e in events.values()),
            "generated_tokens": sum(e["raw"].get("eval_count", 0) for e in events.values())}
        checks[stage + ":aggregate_usage"] = analysis["actor_usage"][stage] == usage
        plan = read(out / stage / "manifest.json")["order"]
        for condition in ("P1", "P2"):
            selected = [events[cell["id"]] for cell in plan if cell["condition"] == condition]
            times = [e["elapsed_seconds"] for e in selected]
            resources.setdefault(stage, {})[condition] = {"calls": len(selected), "request_seconds": sum(times),
                "mean_seconds": fmean(times), "median_seconds": median(times),
                "input_tokens": sum(e["raw"].get("prompt_eval_count", 0) for e in selected),
                "generated_tokens": sum(e["raw"].get("eval_count", 0) for e in selected)}
    reviewer_usage = {name: sum(t["summary"][name] for t in all_traces) for name in analysis["reviewer_usage"]}
    checks["reviewer_usage_and_cost_estimate"] = reviewer_usage == analysis["reviewer_usage"] and math.isclose(analysis["user_rate_estimated_usd"], reviewer_usage["inputTokens"] * 0.04 / 1_000_000)
    checks["original_white_paper_preserved"] = sha(ROOT / "docs/know_thyself_operational_metasubstrate_white_paper.docx") == "cd2e5ba0cd8c79f01e9373e8254421aaa849c25305229123b7a0959e6d8a1f14"
    old_audit = read(ROOT / "results/2026-10-03-failure-audit/evidence.json")
    checks["original_prompt_only_study_sources_preserved"] = all(sha(ROOT / name) == expected for name, expected in old_audit["source_hashes"].items())
    output = {"created_at": stamp(), "all_pass": all(checks.values()), "checks": checks,
        "actor_attempts": sum(len(rows) for rows in ends.values()), "actor_request_seconds": total_seconds,
        "pre_output_passes": {stage: sum(e["raw"].get("pre_output_audit", {}).get("pass", False) for e in rows.values()) for stage, rows in ends.items()},
        "reason_present_final": sum(row["reason_present"] for row in analysis["rows"]),
        "largest_input_plus_generated": max(e["raw"].get("prompt_eval_count", 0) + e["raw"].get("eval_count", 0) for rows in ends.values() for e in rows.values()),
        "analysis_sha256": sha(out / "balanced-analysis.json"), "verifier_sha256": sha(Path(__file__)), "payload_scoped_safety_rows": safety_rows,
        "family_summary": families, "resource_summary": resources,
        "semantic_choice_counts": {phase: dict(Counter(r.get("choice", "missing") for reviews in recovered[phase].values() for r in reviews)) for phase in recovered}}
    (out / "verification.json").write_text(json.dumps(output, indent=2) + "\n")
    if not output["all_pass"]:
        raise ValueError("Balanced matrix verification failed")
    return output


def main() -> None:
    """Recheck saved inference and print compact audit results."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    value = verify(args.run.resolve())
    print(json.dumps({key: value[key] for key in ("all_pass", "actor_attempts", "actor_request_seconds", "pre_output_passes", "reason_present_final", "largest_input_plus_generated")}, indent=2))


if __name__ == "__main__":
    main()
