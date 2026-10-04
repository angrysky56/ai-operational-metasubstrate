"""Audit the completed matched feedback run without new model requests.

Integrity and protocol adherence are separate: a preserved protocol deviation
must remain visible even when a subsequent extraction repair is correct.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path

from analyze_challenge_test import final_payload
from grade_challenge import grade
from jev_review_records import complete_reviews
from run_ollama import messages_for, stamp
from visible_plan_validator import gate, review_fields, validate

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    """Hash preserved bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path: Path) -> dict:
    """Load a local JSON artifact."""
    return json.loads(path.read_text())


def result(path: Path) -> dict:
    """Require a successful saved MCP envelope."""
    value = read(path)
    if value.get("isError"):
        raise ValueError("Recorded MCP error: " + path.name)
    return value["structuredContent"]["result"]


def verify(run: Path) -> dict:
    """Check actor inputs, immutable studies, full traces and repaired decisions."""
    initial_lock, mechanism, correction_lock = [read(run / name) for name in
        ("initial-input-lock.json", "mechanism-lock.json", "correction-input-lock.json")]
    initial_data, correction_data = [read(run / name) for name in ("initial-dataset.json", "correction-dataset.json")]
    checks = {
        "initial_dataset_frozen": sha(run / "initial-dataset.json") == initial_lock["dataset_sha256"] == mechanism["initial_dataset_sha256"],
        "correction_dataset_frozen": sha(run / "correction-dataset.json") == correction_lock["dataset_sha256"],
        "mechanism_lock_frozen": sha(run / "mechanism-lock.json") == correction_lock["mechanism_lock_sha256"],
        "shared_initial_events_frozen": sha(run / "initial/events.jsonl") == correction_lock["initial_events_sha256"],
        "initial_review_result_frozen": sha(run / "initial-review-result.json") == correction_lock["review_result_sha256"],
    }
    for prefix, lock in (("initial", initial_lock), ("mechanism", mechanism)):
        for name, expected in lock["source_hashes"].items():
            checks[prefix + ":frozen:" + name] = sha(run / ("frozen-" + prefix + "-" + Path(name).name)) == expected
    digests, backends, ends_by_stage, usage = set(), set(), {}, {}
    options = {"temperature": 0, "seed": 42, "num_predict": 8192, "num_ctx": 16384, "top_k": 20, "top_p": 0.95}
    for stage, data, count, seed in (("initial", initial_data, 6, 20261011), ("corrections", correction_data, 18, 20261012)):
        directory = run / stage
        manifest = read(directory / "manifest.json")
        config = manifest["config"]
        digests.add(config["digest"])
        backends.add(json.dumps(config["backend"], sort_keys=True))
        checks[stage + ":settings"] = config["options"] == options and config["think"] is True and config["order_seed"] == seed and config["max_attempts"] == count
        checks[stage + ":dataset"] = sha(directory / "dataset.json") == config["dataset_sha256"] == sha(run / ("initial-dataset.json" if stage == "initial" else "correction-dataset.json"))
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
        starts = [e for e in events if e["event"] == "started"]
        ends = [e for e in events if e["event"] == "finished"]
        checks[stage + ":accounting"] = len(starts) == len(ends) == count and len({e["cell"] for e in starts}) == count and len({e["cell"] for e in ends}) == count and {e["attempt"] for e in starts} == {e["attempt"] for e in ends}
        cells = {cell["id"]: cell for cell in manifest["order"]}
        checks[stage + ":visible_messages"] = all(e["request"]["messages"] == messages_for(data, cells[e["cell"]]) and e["request"]["options"] == options and e["request"]["think"] is True for e in starts)
        checks[stage + ":planned_cells"] = set(cells) == {c["id"] + "-P1" for c in data["cases"]} == {e["cell"] for e in ends}
        ends_by_stage[stage] = {e["cell"]: e for e in ends}
        usage[stage] = {"attempts": len(ends), "complete": sum(e["status"] == "complete" for e in ends),
            "request_seconds": sum(e["elapsed_seconds"] for e in ends),
            "input_tokens": sum(e["raw"].get("prompt_eval_count", 0) for e in ends),
            "generated_tokens": sum(e["raw"].get("eval_count", 0) for e in ends),
            "nonempty_thinking": sum(bool(e["raw"].get("message", {}).get("thinking", "")) for e in ends),
            "largest_input_plus_generated": max(e["raw"].get("prompt_eval_count", 0) + e["raw"].get("eval_count", 0) for e in ends)}
    checks["same_actor_digest_and_backend"] = len(digests) == len(backends) == 1
    checks["actor_time_budget"] = sum(u["request_seconds"] for u in usage.values()) <= 7200
    checks["correction_remaining_budget"] = read(run / "corrections/manifest.json")["config"]["max_seconds"] == 7200 - math.ceil(usage["initial"]["request_seconds"])
    for case in initial_data["cases"]:
        variants = {c["feedback_arm"]: c for c in correction_data["cases"] if c["origin_case"] == case["id"]}
        initial = ends_by_stage["initial"][case["id"] + "-P1"]
        history = case.get("history", []) + [{"role": "user", "content": case["prompt"]}, {"role": "assistant", "content": initial["raw"]["message"]["content"]}]
        checks[case["id"] + ":shared_forks"] = set(variants) == {"SELF", "CODE", "JEV"} and all(v["history"] == history for v in variants.values())
        checks[case["id"] + ":nested_feedback"] = variants["JEV"]["prompt"].startswith(variants["CODE"]["prompt"]) and variants["CODE"]["prompt"].startswith(variants["SELF"]["prompt"])
    recovered, summaries, models, coverage = {}, [], set(), {}
    for stage in ("initial", "final"):
        request = read(run / (stage + "-review-request.json"))
        bindings = read(run / (stage + "-review-bindings.json"))
        trace = result(run / (stage + "-trace-result.json"))
        preview = result(run / (stage + "-review-result.json"))
        full = complete_reviews(trace, request["items"], bindings["bindings"], mechanism["capability"])
        recovered[stage] = full
        summaries.append(trace["summary"])
        for reviews in full.values():
            models.update(r["returned_model"] for r in reviews if r["status"] == "complete")
        original = read(run / (stage + "-reviews.json"))["by_case"]
        coverage[stage] = {"requested": len(request["items"]), "preview": len(preview["results"]),
            "original_extracted": sum(map(len, original.values())), "recovered": sum(map(len, full.values()))}
        checks[stage + ":bounded_review_inputs"] = len(request["items"]) <= 12 and request["context"] == {} and request["useCache"] is False and request["maxCalls"] == len(request["items"]) and all(set(item["data"]) == {"field_path", "field_value", "reason"} for item in request["items"])
        checks[stage + ":complete_trace_and_identity"] = len(bindings["bindings"]) == len(request["items"]) == sum(map(len, full.values())) and preview["capability"] == mechanism["capability"]
        for case in initial_data["cases"]:
            event = ends_by_stage["initial"][case["id"] + "-P1"] if stage == "initial" else ends_by_stage["corrections"][case["id"] + "-JEV-P1"]
            valid = validate(case["family"], case["prompt"], event["raw"]["message"].get("content", ""), event["status"] == "complete")
            checks[stage + ":exact_validation:" + case["id"]] = valid == bindings["validations"][case["id"]]
            selected = [item["data"] for item in request["items"] if bindings["bindings"][item["id"]]["case_id"] == case["id"]]
            checks[stage + ":exact_review_fields:" + case["id"]] = selected == review_fields(valid)
    repair = run / "coverage-repair"
    repaired = read(repair / "feedback-analysis.json")
    original_analysis = read(run / "feedback-analysis.json")
    checks["payload_scores_preserved"] = all((a["case_id"], a["arm"], a["success"], a["payload"]) == (b["case_id"], b["arm"], b["success"], b["payload"]) for a, b in zip(original_analysis["rows"], repaired["rows"], strict=True))
    checks["initial_recovered_reviews_exact"] = read(repair / "initial-reviews.json")["by_case"] == recovered["initial"]
    checks["final_recovered_reviews_exact"] = read(repair / "final-reviews.json")["by_case"] == recovered["final"]
    for row in repaired["rows"]:
        case = next(c for c in initial_data["cases"] if c["id"] == row["case_id"])
        event = ends_by_stage["corrections"][row["case_id"] + "-" + row["arm"] + "-P1"]
        try:
            payload, _ = final_payload(event["raw"]["message"].get("content", ""))
            keyed_success = grade(json.dumps(payload), case["checks"])["success"] if event["status"] == "complete" else 0
        except ValueError:
            keyed_success = 0
        checks[row["case_id"] + ":independent_keyed_score:" + row["arm"]] = row["success"] == keyed_success
        validation = validate(case["family"], case["prompt"], event["raw"]["message"].get("content", ""), event["status"] == "complete")
        checks[row["case_id"] + ":recovered_gate:" + row["arm"]] = row["gate"] == gate(validation, recovered["final"].get(row["case_id"], []), require_reviews=row["arm"] == "JEV")
    audit = read(ROOT / "results/2026-10-03-failure-audit/evidence.json")
    checks["earlier_study_sources_preserved"] = all(sha(ROOT / name) == expected for name, expected in audit["source_hashes"].items())
    checks["original_white_paper_preserved"] = sha(ROOT / "docs/know_thyself_operational_metasubstrate_white_paper.docx") == "cd2e5ba0cd8c79f01e9373e8254421aaa849c25305229123b7a0959e6d8a1f14"
    checks["repair_original_artifacts_frozen"] = all(sha(run / name) == expected for name, expected in read(repair / "repair-lock.json")["original_artifact_sha256"].items())
    inputs = sum(s["inputTokens"] for s in summaries)
    output = {"created_at": stamp(), "integrity_pass": all(checks.values()), "checks": checks,
        "protocol_complete": all(c["requested"] == c["original_extracted"] for c in coverage.values()),
        "deviation": "Original extraction used the five-item immediate preview; missing initial feedback cannot be retroactively supplied. Saved final judgments were recovered without new inference.",
        "review_coverage": coverage, "actor_usage": usage, "returned_reviewer_models": sorted(models),
        "reviewer_model_calls": sum(s["modelCalls"] for s in summaries), "reviewer_http_attempts": sum(s["httpAttempts"] for s in summaries),
        "reviewer_input_tokens": inputs, "reviewer_output_tokens": sum(s["outputTokens"] for s in summaries),
        "unreported_cost_calls": sum(s["unreportedCosts"] for s in summaries),
        "user_rate_estimated_usd": inputs * 0.04 / 1_000_000,
        "cost_status": "User supplied $0.04/million input and $0 output; estimate is not provider billing.",
        "verifier_sha256": sha(Path(__file__)), "repaired_analysis_sha256": sha(repair / "feedback-analysis.json")}
    (run / "verification.json").write_text(json.dumps(output, indent=2) + "\n")
    if not output["integrity_pass"]:
        raise ValueError("Feedback integrity verification failed")
    return output


def main() -> None:
    """Print compact verification and save the full evidence."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    value = verify(args.run.resolve())
    print(json.dumps({key: item for key, item in value.items() if key != "checks"}, indent=2))


if __name__ == "__main__":
    main()
