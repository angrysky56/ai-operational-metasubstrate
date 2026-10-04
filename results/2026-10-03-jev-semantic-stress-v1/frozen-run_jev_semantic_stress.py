"""Run a frozen twelve-case semantic boundary check, or verify saved results."""

import argparse
import json
from pathlib import Path

from feedback_harness import CAPABILITY, mcp, save, sha
from jev_review_records import complete_reviews
from run_ollama import stamp
from visible_plan_validator import validate

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ["scripts/run_jev_semantic_stress.py", "scripts/jev_review_records.py", "scripts/feedback_harness.py",
           "scripts/visible_plan_validator.py", "harness/jev-client.ts", "harness/package-lock.json",
           "data/jev-semantic-stress-v1.json", "docs/jev-semantic-stress-protocol.md"]


def execute(out: Path, server: str, verify_only: bool) -> dict:
    """Separate frozen labels from twelve narrow runtime requests."""
    out.mkdir(parents=True, exist_ok=True)
    dataset = json.loads((ROOT / "data/jev-semantic-stress-v1.json").read_text())
    hashes = {name: sha(ROOT / name) for name in SOURCES}
    lock_path = out / "precollection-lock.json"
    if lock_path.exists():
        lock = json.loads(lock_path.read_text())
        if lock["source_hashes"] != hashes:
            raise ValueError("Frozen stress-check source changed")
    elif verify_only:
        raise ValueError("No saved stress-check run to verify")
    else:
        lock = {"created_at": stamp(), "source_hashes": hashes, "capability": CAPABILITY,
                "semantic_item_limit": 12, "actor_attempt_limit": 0}
        save(lock_path, lock)
        for name in SOURCES:
            (out / ("frozen-" + Path(name).name)).write_bytes((ROOT / name).read_bytes())
    save(out / "dataset.json", dataset)
    cases = dataset["cases"]
    if len(cases) != 12 or len({case["id"] for case in cases}) != 12:
        raise ValueError("Twelve unique stress cases required")
    items = [{"id": case["id"], "data": case["data"]} for case in cases]
    request = {"name": CAPABILITY["name"], "version": CAPABILITY["version"], "items": items,
               "context": {}, "maxCalls": 12, "useCache": False}
    save(out / "review-request.json", request)
    if not verify_only:
        definition = mcp(out, "get_capability", "definition-request.json", "definition-result.json",
                         {"name": CAPABILITY["name"], "version": CAPABILITY["version"]}, server)
        if any(definition[key] != value for key, value in CAPABILITY.items()):
            raise ValueError("Reviewer identity changed")
        response = mcp(out, "run_capability", "review-request.json", "review-result.json", request, server)
        mcp(out, "get_run", "trace-request.json", "trace-result.json",
            {"runId": response["runId"], "details": True, "limit": 20}, server)
    trace_envelope = json.loads((out / "trace-result.json").read_text())
    if trace_envelope.get("isError"):
        raise ValueError("Recorded trace error")
    trace = trace_envelope["structuredContent"]["result"]
    bindings = {case["id"]: {"case_id": case["id"]} for case in cases}
    reviews = complete_reviews(trace, items, bindings, CAPABILITY)
    rows = []
    for case in cases:
        review = reviews[case["id"]][0]
        rows.append({"id": case["id"], "expected": case["expected"], **review,
                     "pass": review["status"] == "complete" and review["choice"] == case["expected"]})
    source_case = next(case for case in json.loads((ROOT / "data/challenge-dev-v1.json").read_text())["cases"] if case["id"] == "C-S1")
    wrong = json.loads(json.dumps(source_case["checks"]["fields"]))
    wrong["steps"]["Q4"] = "PAUSE"
    wrong["reason"] = cases[-1]["data"]["reason"]
    validation = validate(source_case["family"], source_case["prompt"], json.dumps(wrong))
    trace_items = {row["id"]: row for row in trace["items"]}
    checks = {"all_frozen_snapshots": all(sha(out / ("frozen-" + Path(name).name)) == expected for name, expected in hashes.items()),
              "exact_provider_state": all(trace_items[item["id"]]["events"][0]["request"]["state"] == {"item": item["data"], "context": {}, "prior": {}} for item in items),
              "twelve_new_calls": trace["summary"]["modelCalls"] == 12 and trace["summary"]["cacheHits"] == 0,
              "wrong_source_still_rejected_by_code": not validation["valid"] and "steps.Q4" in validation["failed_checks"]}
    summary = trace["summary"]
    result = {"created_at": lock["created_at"], "scope": dataset["scope"], "integrity_pass": all(checks.values()), "checks": checks,
              "passed": sum(row["pass"] for row in rows), "planned": 12, "rows": rows,
              "missed_contradictions": [row["id"] for row in rows if row["expected"] == "contradicts_payload" and not row["pass"]],
              "false_contradiction_flags": [row["id"] for row in rows if row["expected"] != "contradicts_payload" and row.get("choice") == "contradicts_payload"],
              "returned_models": sorted({row["returned_model"] for row in rows if row["status"] == "complete"}),
              "summary": summary, "user_rate_estimated_usd": summary["inputTokens"] * 0.04 / 1_000_000,
              "cost_status": "User supplied input/output rates; monetary billing unreported.",
              "wrong_source_runtime_validation": validation,
              "review_result_sha256": sha(out / "review-result.json"), "trace_sha256": sha(out / "trace-result.json")}
    save(out / "analysis.json", result)
    if not result["integrity_pass"]:
        raise ValueError("Stress-check integrity failed")
    return result


def main() -> None:
    """Run once or verify stored inference without making new requests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--server", default="jev")
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    result = execute(args.output.resolve(), args.server, args.verify_only)
    print(json.dumps({key: result[key] for key in ("integrity_pass", "passed", "planned", "missed_contradictions", "false_contradiction_flags", "returned_models", "user_rate_estimated_usd")}, indent=2))


if __name__ == "__main__":
    main()
