"""Run the repaired, bounded P1/P2 feedback matrix on all 24 reused instances."""

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path

from feedback_harness import CAPABILITY, COMMON, code_feedback, mcp, read_ends, save, score, sha
from jev_review_records import complete_reviews
from run_locked_ollama import pre_output_rule, settings_lock
from run_ollama import stamp
from visible_plan_validator import gate, review_fields, validate

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["scripts/run_balanced_feedback.py", "scripts/run_locked_ollama.py", "scripts/run_ollama.py",
    "scripts/feedback_harness.py", "scripts/jev_review_records.py", "scripts/visible_plan_validator.py",
    "scripts/grade_challenge.py", "scripts/analyze_challenge_test.py", "data/challenge-test-v1.json",
    "data/visible-policy-headers.json", "data/generator-settings-lock.json", "data/pre-output-checks-v1.txt",
    "harness/jev-client.ts", "harness/package.json", "harness/package-lock.json", "docs/balanced-feedback-v2-protocol.md"]


def freeze(out: Path) -> dict:
    """Freeze the entire matrix mechanism before reading any new output."""
    out.mkdir(parents=True, exist_ok=True)
    hashes = {name: sha(ROOT / name) for name in SOURCES}
    lock_path = out / "precollection-lock.json"
    if lock_path.exists():
        lock = json.loads(lock_path.read_text())
        if lock["source_hashes"] != hashes:
            raise ValueError("Frozen balanced matrix source changed")
    else:
        lock = {"created_at": stamp(), "mechanism_version": 2, "source_hashes": hashes,
            "actor_attempt_limit": 96, "semantic_item_limit": 192, "settings": settings_lock(),
            "capability": CAPABILITY, "conditions": ["P1", "P2"], "case_count": 24}
        save(lock_path, lock)
        for name in SOURCES:
            (out / ("frozen-" + Path(name).name)).write_bytes((ROOT / name).read_bytes())
    source = json.loads((ROOT / "data/challenge-test-v1.json").read_text())
    data = {"schema": 1, "stage": "balanced_feedback_initial", "conditions": {
        condition: source["conditions"][condition] + "\n\n" + pre_output_rule() for condition in ("P1", "P2")},
        "cases": source["cases"]}
    if len(data["cases"]) != 24:
        raise ValueError("The complete 24-case matrix is required")
    for case in data["cases"]:
        if not validate(case["family"], case["prompt"], "{}")["supported"]:
            raise ValueError("Unsupported visible policy: " + case["id"])
    save(out / "initial-dataset.json", data)
    return lock


def collect(out: Path, stage: str) -> bool:
    """Collect untouched cells with identical settings and a stage budget."""
    freeze(out)
    ends = read_ends(out / stage)
    if len(ends) == 48:
        return True
    if stage == "initial":
        dataset, budget, order_seed = out / "initial-dataset.json", 7200, 20261013
    else:
        dataset, order_seed = out / "correction-dataset.json", 20261014
        locked = json.loads((out / "correction-input-lock.json").read_text())
        if locked["dataset_sha256"] != sha(dataset) or locked["initial_events_sha256"] != sha(out / "initial/events.jsonl"):
            raise ValueError("Correction inputs changed")
        budget = 14400 - math.ceil(sum(e["elapsed_seconds"] for e in read_ends(out / "initial").values()))
    subprocess.run([sys.executable, str(ROOT / "scripts/run_locked_ollama.py"), "--model", settings_lock()["model"],
        "--dataset", str(dataset), "--output", str(out / stage), "--max-attempts", "48", "--limit-new", "48",
        "--max-seconds", str(budget), "--request-timeout", "900", "--order-seed", str(order_seed)], check=True)
    return len(read_ends(out / stage)) == 48


def candidates(out: Path, stage: str) -> list[dict]:
    """Bind each condition's actual candidate to original visible records."""
    data = json.loads((out / "initial-dataset.json").read_text())
    directory = "initial" if stage == "initial" else "corrections"
    ends = read_ends(out / directory)
    found = []
    for case in data["cases"]:
        for condition in ("P1", "P2"):
            pair = case["id"] + "-" + condition
            cell = pair if stage == "initial" else pair + "-feedback-" + condition
            event = ends[cell]
            answer = event["raw"].get("message", {}).get("content", "")
            found.append({"pair": pair, "case_id": case["id"], "condition": condition,
                "family": case["family"], "source_prompt": case["prompt"], "answer": answer,
                "complete": event["status"] == "complete"})
    return found


def review(out: Path, stage: str, server: str) -> dict:
    """Review at most two fields per candidate in complete twelve-item batches."""
    found = candidates(out, stage)
    bindings, validations, items = {}, {}, []
    for candidate in found:
        validation = validate(candidate["family"], candidate["source_prompt"], candidate["answer"], candidate["complete"])
        validations[candidate["pair"]] = validation
        for index, field in enumerate(review_fields(validation)):
            item_id = candidate["pair"].replace("-", "_") + "_" + stage + "_" + str(index)
            items.append({"id": item_id, "data": field})
            bindings[item_id] = {"case_id": candidate["pair"], "field_path": field["field_path"],
                "candidate_sha256": validation["candidate_sha256"], "source_sha256": validation["source_sha256"]}
    if len(items) > 96:
        raise ValueError("Semantic item budget exceeded")
    save(out / (stage + "-review-bindings.json"), {"bindings": bindings, "validations": validations})
    recovered = {candidate["pair"]: [] for candidate in found}
    for batch, offset in enumerate(range(0, len(items), 12), 1):
        part = items[offset:offset + 12]
        prefix = stage + "-batch-" + f"{batch:02}"
        request = {"name": CAPABILITY["name"], "version": 1, "items": part, "context": {},
                   "maxCalls": len(part), "useCache": False}
        response = mcp(out, "run_capability", prefix + "-request.json", prefix + "-result.json", request, server)
        if response["capability"] != CAPABILITY:
            raise ValueError("Reviewer capability changed")
        trace = mcp(out, "get_run", prefix + "-trace-request.json", prefix + "-trace.json",
                    {"runId": response["runId"], "details": True, "limit": 20}, server)
        if trace["runId"] != response["runId"]:
            raise ValueError("Stored trace belongs to another batch")
        rows = complete_reviews(trace, part, {item["id"]: bindings[item["id"]] for item in part}, CAPABILITY)
        for pair, reviews in rows.items():
            recovered[pair].extend(reviews)
    save(out / (stage + "-reviews.json"), {"by_pair": recovered})
    return recovered


def prepare(out: Path, server: str) -> None:
    """Freeze equally assisted, condition-matched correction conversations."""
    freeze(out)
    if len(read_ends(out / "initial")) != 48:
        raise ValueError("All 48 initial terminal cells are required")
    definition = mcp(out, "get_capability", "definition-request.json", "definition-result.json",
                     {"name": CAPABILITY["name"], "version": 1}, server)
    if any(definition[key] != value for key, value in CAPABILITY.items()):
        raise ValueError("Pinned reviewer changed")
    reviews = review(out, "initial", server)
    original = json.loads((out / "initial-dataset.json").read_text())
    ends = read_ends(out / "initial")
    dataset = {"schema": 1, "stage": "balanced_feedback_corrections", "conditions": original["conditions"], "cases": []}
    for case in original["cases"]:
        for condition in ("P1", "P2"):
            pair = case["id"] + "-" + condition
            event = ends[pair]
            answer = event["raw"].get("message", {}).get("content", "")
            validation = validate(case["family"], case["prompt"], answer, event["status"] == "complete")
            reason = (validation["payload"] or {}).get("reason")
            notes = [{key: row[key] for key in ("field_path", "status", "choice", "confidence") if key in row} for row in reviews[pair]]
            feedback = COMMON + "\nPrior generation status: " + event["status"] + "." + code_feedback(validation)
            feedback += "\nRequired final reason present: " + str(isinstance(reason, str) and bool(reason.strip())) + "."
            feedback += "\nNarrow semantic field/explanation consistency reviews; these do not prove source truth:\n" + json.dumps(notes, sort_keys=True)
            dataset["cases"].append({"id": pair + "-feedback", "conditions": [condition], "origin_case": case["id"],
                "actor_condition": condition, "family": case["family"], "prompt": feedback,
                "history": case.get("history", []) + [{"role": "user", "content": case["prompt"]}, {"role": "assistant", "content": answer}],
                "checks": case["checks"], "key": case["key"], "requirements": case.get("requirements", []), "metric_scope": {}})
    save(out / "correction-dataset.json", dataset)
    save(out / "correction-input-lock.json", {"initial_events_sha256": sha(out / "initial/events.jsonl"),
        "dataset_sha256": sha(out / "correction-dataset.json"), "precollection_lock_sha256": sha(out / "precollection-lock.json"),
        "initial_reviews_sha256": sha(out / "initial-reviews.json")})


def analyze(out: Path) -> dict:
    """Keep keyed correctness, review consistency and accepted deliverables separate."""
    freeze(out)
    data = json.loads((out / "initial-dataset.json").read_text())
    initials, finals = read_ends(out / "initial"), read_ends(out / "corrections")
    reviews = {stage: json.loads((out / (stage + "-reviews.json")).read_text())["by_pair"] for stage in ("initial", "final")}
    rows = []
    for case in data["cases"]:
        for condition in ("P1", "P2"):
            pair = case["id"] + "-" + condition
            initial, final = initials[pair], finals[pair + "-feedback-" + condition]
            initial_score, final_score = score(initial, case["checks"]), score(final, case["checks"])
            answer = final["raw"].get("message", {}).get("content", "")
            validation = validate(case["family"], case["prompt"], answer, final["status"] == "complete")
            reason = (validation["payload"] or {}).get("reason")
            reason_present = isinstance(reason, str) and bool(reason.strip())
            decision = gate(validation, reviews["final"][pair], require_reviews=True) if reason_present else {"accepted": False, "reason": "missing_required_reason"}
            contradictory = lambda phase: any(r.get("choice") == "contradicts_payload" and r.get("confidence", 0) >= 0.8 for r in reviews[phase][pair])
            rows.append({"case_id": case["id"], "family": case["family"], "condition": condition,
                "initial_success": initial_score["success"], "final_success": final_score["success"],
                "initial_status": initial["status"], "final_status": final["status"],
                "payload": final_score.get("payload"), "reason_present": reason_present,
                "pre_output_pass": final["raw"].get("pre_output_audit", {}).get("pass", False),
                "runtime_valid": validation["valid"], "gate": decision,
                "initial_contradiction": contradictory("initial"), "final_contradiction": contradictory("final"),
                "initial_reviews": reviews["initial"][pair], "final_reviews": reviews["final"][pair]})
    totals = {}
    for condition in ("P1", "P2"):
        selected = [row for row in rows if row["condition"] == condition]
        totals[condition] = {"planned": 24, "initial_success": sum(r["initial_success"] for r in selected),
            "final_success": sum(r["final_success"] for r in selected),
            "repairs": sum(not r["initial_success"] and r["final_success"] for r in selected),
            "regressions": sum(r["initial_success"] and not r["final_success"] for r in selected),
            "accepted": sum(r["gate"]["accepted"] for r in selected),
            "wrong_accepted": sum(r["gate"]["accepted"] and not r["final_success"] for r in selected),
            "correct_withheld": sum(not r["gate"]["accepted"] and r["final_success"] for r in selected),
            "initial_contradictions": sum(r["initial_contradiction"] for r in selected),
            "final_contradictions": sum(r["final_contradiction"] for r in selected),
            "incomplete_initial": sum(r["initial_status"] != "complete" for r in selected),
            "incomplete_final": sum(r["final_status"] != "complete" for r in selected)}
    paired = {"both_pass": 0, "P1_only": 0, "P2_only": 0, "both_fail": 0}
    for case in data["cases"]:
        pair_rows = {row["condition"]: row for row in rows if row["case_id"] == case["id"]}
        p1, p2 = (pair_rows[c]["final_success"] for c in ("P1", "P2"))
        paired["both_pass" if p1 and p2 else "P1_only" if p1 else "P2_only" if p2 else "both_fail"] += 1
    traces = [json.loads(path.read_text())["structuredContent"]["result"] for path in sorted(out.glob("*-batch-*-trace.json"))]
    result = {"created_at": stamp(), "scope": "Reused 24 instances, P1/P2 with equal code/Jev feedback and one correction; exploratory only.",
        "totals": totals, "paired_final": paired, "P2_minus_P1_pp": 100 * (totals["P2"]["final_success"] - totals["P1"]["final_success"]) / 24,
        "rows": rows, "runtime_keyed_disagreements": [r["case_id"] + "-" + r["condition"] for r in rows if bool(r["final_success"]) != r["runtime_valid"]],
        "reviewer_usage": {key: sum(trace["summary"][key] for trace in traces) for key in ("modelCalls", "httpAttempts", "inputTokens", "outputTokens", "unreportedCosts", "cacheHits")},
        "reviewer_models": sorted({event["response"]["model"] for trace in traces for item in trace["items"] for event in item["events"] if event.get("response")}),
        "actor_usage": {stage: {"calls": len(events), "request_seconds": sum(e["elapsed_seconds"] for e in events.values()),
            "input_tokens": sum(e["raw"].get("prompt_eval_count", 0) for e in events.values()),
            "generated_tokens": sum(e["raw"].get("eval_count", 0) for e in events.values())} for stage, events in (("initial", initials), ("corrections", finals))}}
    result["user_rate_estimated_usd"] = result["reviewer_usage"]["inputTokens"] * 0.04 / 1_000_000
    (out / "balanced-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("totals", "paired_final", "reviewer_usage")}, indent=2))
    return result


def main() -> None:
    """Run explicit stages; stop collection for review without retrying a cell."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--stage", choices=("freeze", "initial", "prepare", "corrections", "finish", "analyze", "all"), default="all")
    parser.add_argument("--server", default="jev")
    args = parser.parse_args()
    out = args.output.resolve()
    freeze(out)
    if args.stage in ("initial", "all") and not collect(out, "initial"):
        print("Initial collection paused; inspect the terminal event before resuming untouched cells.")
        return
    if args.stage in ("prepare", "all"):
        prepare(out, args.server)
    if args.stage in ("corrections", "all") and not collect(out, "corrections"):
        print("Correction collection paused; inspect the terminal event before resuming untouched cells.")
        return
    if args.stage in ("finish", "all"):
        if len(read_ends(out / "corrections")) != 48:
            raise ValueError("All 48 correction cells are required")
        review(out, "final", args.server)
        analyze(out)
    elif args.stage == "analyze":
        analyze(out)


if __name__ == "__main__":
    main()
