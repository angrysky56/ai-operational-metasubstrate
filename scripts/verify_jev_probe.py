"""Verify the recorded MCP semantic-review probe without making model calls."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    """Hash preserved study sources."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_result(path: Path) -> dict:
    """Require the server's structured success envelope."""
    value = json.loads(path.read_text())
    if value.get("isError"):
        raise ValueError(f"MCP error in {path.name}")
    return value["structuredContent"]["result"]


def main() -> None:
    """Check exact semantic inputs, kept-out labels and saved-version identity."""
    run = ROOT / "results/2026-10-03-jev-probe"
    lock = json.loads((run / "payload-probe-lock.json").read_text())
    checks = {
        "original_analysis_preserved": sha(ROOT / "results/2026-10-03-challenge-test-v1/challenge-analysis.json") == lock["source_sha256"],
        "builder_preserved": sha(ROOT / "scripts/build_jev_payload_probe.py") == lock["builder_sha256"],
    }
    for name, expected in lock["input_sha256"].items():
        checks[name + ":frozen"] = sha(run / name) == expected
    definition = json.loads((run / "payload-capability.json").read_text())["definition"]
    saved = read_result(run / "payload-capability-saved.json")
    checks["saved_definition_exact"] = saved["definition"] == definition and saved["version"] == 1
    evaluation = read_result(run / "payload-evaluation-result.json")
    trace = read_result(run / "payload-evaluation-trace.json")
    source_cases = json.loads((run / "payload-evaluation.json").read_text())["cases"]
    items = {item["id"]: item for item in trace["items"]}
    checks["all_six_unique_cases_recorded"] = len(items) == len(trace["items"]) == 6 and set(items) == {c["id"] for c in source_cases}
    computed_passed = 0
    concrete_models = set()
    for case in source_cases:
        item = items[case["id"]]
        events = item["events"]
        checks[case["id"] + ":single_stage"] = len(events) == 1
        event = events[0]
        checks[case["id"] + ":visible_state_only"] = event["request"]["state"] == {"item": case["data"], "context": {}, "prior": {}}
        checks[case["id"] + ":exact_question"] = event["request"]["questions"] == definition["stages"][0]["questions"]
        checks[case["id"] + ":fresh"] = not event["cached"]
        concrete_models.add(event["response"]["model"])
        answer = item["result"]["stages"]["review"]["answers"]["relation"]["choice"]
        computed_passed += answer == case["expected"][0]["value"]
    checks["reported_scores_recompute"] = computed_passed == evaluation["evaluation"]["passed"] and evaluation["evaluation"]["total"] == 6
    claim_trace = read_result(run / "claim-review-trace.json")
    for item in claim_trace["items"]:
        for event in item["events"]:
            concrete_models.add(event["response"]["model"])
    summaries = [trace["summary"], claim_trace["summary"]]
    result = {"created_at": datetime.now(timezone.utc).isoformat(), "all_pass": all(checks.values()),
              "checks": checks, "authored_semantic_checks_passed": computed_passed, "authored_semantic_checks_total": 6,
              "provider": trace["manifest"]["provider"], "requested_model": trace["manifest"]["model"],
              "returned_models": sorted(concrete_models),
              "total_model_calls": sum(s["modelCalls"] for s in summaries),
              "total_http_attempts": sum(s["httpAttempts"] for s in summaries),
              "cost_status": "Provider did not report monetary cost; zero aggregate reported cost is not evidence of free inference.",
              "unreported_cost_calls": sum(s["unreportedCosts"] for s in summaries),
              "verifier_sha256": sha(Path(__file__)),
              "artifact_sha256": {p.name: sha(p) for p in run.glob("*.json") if p.name != "verification.json"}}
    (run / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    if not result["all_pass"]:
        raise ValueError("Probe verification failed")
    print(json.dumps({key: result[key] for key in ["all_pass", "authored_semantic_checks_passed", "authored_semantic_checks_total", "provider", "returned_models", "total_model_calls", "unreported_cost_calls"]}, indent=2))


if __name__ == "__main__":
    main()
