"""Run matched feedback forks with a visible-record validator and optional Jev.

MCP uses a project-owned SDK adapter and the host's server configuration, with no
imports from another repository. Study grading remains separate from feedback.
"""

import argparse
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

from analyze_challenge_test import final_payload
from grade_challenge import grade
from jev_review_records import complete_reviews
from run_ollama import stamp
from visible_plan_validator import checksum, gate, review_fields, validate

ROOT = Path(__file__).resolve().parents[1]
CAPABILITY = {"name": "omkt_payload_consistency", "version": 1,
              "hash": "3d4ee30843872289b08aee9c74e22cb65db405631b0fa6b06cc1ebe799623544"}
SOURCES = ["scripts/feedback_harness.py", "scripts/visible_plan_validator.py", "scripts/jev_review_records.py", "scripts/run_ollama.py",
           "scripts/grade_challenge.py", "scripts/analyze_challenge_test.py", "data/visible-policy-headers.json",
           "harness/jev-client.ts", "harness/package.json", "harness/package-lock.json",
           "docs/feedback-development-protocol.md"]
COMMON = """Independently recheck the original task's sources, current records, policy,
constraints and the actual submitted JSON fields. Correct mistakes in the plan,
not just the explanation. Preserve correct decisions when no change is warranted.
Return an actual complete replacement JSON object, even if it is unchanged.
An optional reason is allowed. This is your one correction opportunity; do not
execute anything or invent new evidence. A previous explanation is not evidence
that a check succeeded. Use the original task's records and permissions."""


def sha(path: Path) -> str:
    """Hash source and artifact bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    """Create an immutable stage artifact; exact existing content may be reused."""
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text() != text:
            raise ValueError("Refusing to replace frozen artifact: " + path.name)
    else:
        path.write_text(text)


def read_ends(run: Path) -> dict:
    """Refuse uncertain starts or repeated terminal cells."""
    path = run / "events.jsonl"
    if not path.exists():
        return {}
    events = [json.loads(line) for line in path.read_text().splitlines()]
    starts = [e for e in events if e["event"] == "started"]
    ends = [e for e in events if e["event"] == "finished"]
    if len({e["attempt"] for e in starts}) != len(starts) or len({e["cell"] for e in ends}) != len(ends):
        raise ValueError("Repeated attempt/cell")
    if {e["attempt"] for e in starts} != {e["attempt"] for e in ends}:
        raise ValueError("Uncertain request; never resubmit")
    return {e["cell"]: e for e in ends}


def freeze_mechanism(out: Path) -> dict:
    """Freeze all feedback/analysis code before reading newly generated answers."""
    path = out / "mechanism-lock.json"
    hashes = {name: sha(ROOT / name) for name in SOURCES}
    if path.exists():
        lock = json.loads(path.read_text())
        if lock["source_hashes"] != hashes or lock["initial_dataset_sha256"] != sha(out / "initial-dataset.json"):
            raise ValueError("Frozen mechanism source changed")
        return lock
    lock = {"created_at": stamp(), "mechanism_version": 2, "source_hashes": hashes, "capability": CAPABILITY,
            "initial_dataset_sha256": sha(out / "initial-dataset.json"), "correction_arms": ["SELF", "CODE", "JEV"],
            "actor_attempt_limit": 24, "semantic_item_limit": 24, "shared_initials": True}
    for name in SOURCES:
        (out / ("frozen-mechanism-" + Path(name).name)).write_bytes((ROOT / name).read_bytes())
    path.write_text(json.dumps(lock, indent=2) + "\n")
    return lock


def mcp(out: Path, operation: str, request_name: str, result_name: str, request: dict, server: str) -> dict:
    """Call the portable SDK once; uncertain starts block repeat requests."""
    source, result = out / request_name, out / result_name
    save(source, request)
    if not result.exists():
        subprocess.run(["node", str(ROOT / "harness/jev-client.ts"), server, operation,
                        str(source), str(result)], check=True, timeout=200)
    value = json.loads(result.read_text())
    if value.get("isError"):
        raise ValueError("MCP tool returned an error; preserve the recorded response")
    return value["structuredContent"]["result"]


def candidates(out: Path, stage: str) -> list[dict]:
    """Build runtime input from visible prompt and final content, not keys."""
    data = json.loads((out / "initial-dataset.json").read_text())
    if stage == "initial":
        ends = read_ends(out / "initial")
        return [{"case_id": c["id"], "family": c["family"], "source_prompt": c["prompt"],
                 "answer": ends[c["id"] + "-P1"]["raw"].get("message", {}).get("content", ""),
                 "complete": ends[c["id"] + "-P1"]["status"] == "complete"} for c in data["cases"]]
    ends = read_ends(out / "corrections")
    return [{"case_id": c["id"], "family": c["family"], "source_prompt": c["prompt"],
             "answer": ends[c["id"] + "-JEV-P1"]["raw"].get("message", {}).get("content", ""),
             "complete": ends[c["id"] + "-JEV-P1"]["status"] == "complete"} for c in data["cases"]]


def semantic_reviews(out: Path, stage: str, server: str) -> dict:
    """Select at most two fields, retain exact bindings and retrieve provider traces."""
    initial = candidates(out, stage)
    items, bindings, validations = [], {}, {}
    for candidate in initial:
        result = validate(candidate["family"], candidate["source_prompt"], candidate["answer"], candidate["complete"])
        validations[candidate["case_id"]] = result
        for index, item in enumerate(review_fields(result)):
            name = candidate["case_id"].replace("-", "_") + "_" + stage + "_" + str(index)
            items.append({"id": name, "data": item})
            bindings[name] = {"case_id": candidate["case_id"], "field_path": item["field_path"],
                              "candidate_sha256": result["candidate_sha256"], "source_sha256": result["source_sha256"]}
    save(out / (stage + "-review-bindings.json"), {"bindings": bindings, "validations": validations})
    reviews = {c["case_id"]: [] for c in initial}
    if items:
        request = {"name": CAPABILITY["name"], "version": CAPABILITY["version"], "items": items,
                   "context": {}, "maxCalls": len(items), "useCache": False}
        response = mcp(out, "run_capability", stage + "-review-request.json", stage + "-review-result.json", request, server)
        if response["capability"] != CAPABILITY:
            raise ValueError("Reviewer definition changed")
        trace = mcp(out, "get_run", stage + "-trace-request.json", stage + "-trace-result.json",
                    {"runId": response["runId"], "details": True, "limit": 20}, server)
        if trace["runId"] != response["runId"]:
            raise ValueError("Stored trace belongs to another run")
        # run_capability.results is a five-item preview, even after completion.
        # Require every requested result from the persisted, bounded trace.
        reviews.update(complete_reviews(trace, items, bindings, CAPABILITY))
    save(out / (stage + "-reviews.json"), {"by_case": reviews})
    return reviews


def code_feedback(result: dict) -> str:
    """Expose actual failures and visible provenance, not a hidden reference map."""
    view = {key: result[key] for key in ("valid", "supported", "failed_checks", "authoritative")}
    if "error" in result:
        view["error"] = result["error"]
    return "\n\nCode check of the actual prior JSON against the original visible records:\n" + json.dumps(view, sort_keys=True)


def prepare(out: Path, server: str) -> None:
    """Pin reviewer and fork exactly shared initial answers into three feedback arms."""
    freeze_mechanism(out)
    original = json.loads((out / "initial-dataset.json").read_text())
    ends = read_ends(out / "initial")
    if len(ends) != 6 or any(e["status"] not in ("complete", "truncated") for e in ends.values()):
        raise ValueError("Six terminal initial answers required; errors need review")
    definition = mcp(out, "get_capability", "reviewer-definition-request.json", "reviewer-definition-result.json",
                     {"name": CAPABILITY["name"], "version": CAPABILITY["version"]}, server)
    if any(definition[key] != value for key, value in CAPABILITY.items()):
        raise ValueError("Pinned reviewer missing or changed")
    reviews = semantic_reviews(out, "initial", server)
    dataset = {"schema": 1, "stage": "matched_feedback_development_corrections",
               "conditions": original["conditions"], "cases": []}
    for case in original["cases"]:
        event = ends[case["id"] + "-P1"]
        answer = event["raw"].get("message", {}).get("content", "")
        result = validate(case["family"], case["prompt"], answer, event["status"] == "complete")
        if not result["supported"]:
            raise ValueError("Unsupported visible policy; do not generate misleading feedback")
        common = COMMON + "\nPrior generation status: " + event["status"] + "."
        history = case.get("history", []) + [{"role": "user", "content": case["prompt"]}, {"role": "assistant", "content": answer}]
        feedback = {"SELF": common, "CODE": common + code_feedback(result)}
        notes = [{key: review[key] for key in ("field_path", "status", "choice", "confidence") if key in review} for review in reviews[case["id"]]]
        feedback["JEV"] = feedback["CODE"] + "\n\nNarrow semantic review of the prior explanation versus its actual fields. These judgments concern consistency, not source truth or permission:\n" + json.dumps(notes, sort_keys=True)
        for arm in ("SELF", "CODE", "JEV"):
            dataset["cases"].append({"id": case["id"] + "-" + arm, "family": case["family"], "origin_case": case["id"],
                "feedback_arm": arm, "prompt": feedback[arm], "history": history,
                "checks": case["checks"], "key": case["key"], "requirements": case.get("requirements", []), "metric_scope": {}})
    save(out / "correction-dataset.json", dataset)
    save(out / "correction-input-lock.json", {"mechanism_lock_sha256": sha(out / "mechanism-lock.json"),
        "initial_events_sha256": sha(out / "initial/events.jsonl"), "dataset_sha256": sha(out / "correction-dataset.json"),
        "review_result_sha256": sha(out / "initial-review-result.json") if (out / "initial-review-result.json").exists() else None})


def collect(out: Path) -> None:
    """Collect untouched corrections with the original actor configuration."""
    freeze_mechanism(out)
    lock = json.loads((out / "correction-input-lock.json").read_text())
    if lock["dataset_sha256"] != sha(out / "correction-dataset.json") or lock["initial_events_sha256"] != sha(out / "initial/events.jsonl"):
        raise ValueError("Frozen correction inputs or shared initials changed")
    source = json.loads((out / "initial/manifest.json").read_text())
    initial_spent = sum(e["elapsed_seconds"] for e in read_ends(out / "initial").values())
    remaining = 7200 - math.ceil(initial_spent)
    subprocess.run([sys.executable, str(ROOT / "scripts/run_ollama.py"), "--model", source["config"]["model"],
        "--output", str(out / "corrections"), "--dataset", str(out / "correction-dataset.json"),
        "--max-attempts", "18", "--limit-new", "18", "--max-seconds", str(remaining),
        "--request-timeout", "900", "--num-ctx", "16384", "--num-predict", "8192",
        "--think", "true", "--order-seed", "20261012"], check=True)


def score(event: dict | None, spec: dict) -> dict:
    """Evaluate separately with frozen keys; never feed this result to the actor."""
    if not event or event["status"] != "complete":
        return {"success": 0, "payload": None, "error": "No complete answer"}
    try:
        payload, count = final_payload(event["raw"]["message"]["content"])
        return grade(json.dumps(payload), spec) | {"object_count": count}
    except ValueError as error:
        return {"success": 0, "payload": None, "error": str(error)}


def analyze(out: Path) -> dict:
    """Report keyed performance and gate acceptance separately for all eighteen forks."""
    original = json.loads((out / "initial-dataset.json").read_text())
    initials, ends = read_ends(out / "initial"), read_ends(out / "corrections")
    review_file = out / "final-reviews.json"
    reviews = json.loads(review_file.read_text())["by_case"] if review_file.exists() else {}
    initial_rows, rows = [], []
    for case in original["cases"]:
        initial = score(initials.get(case["id"] + "-P1"), case["checks"])
        initial_rows.append({"case_id": case["id"], "family": case["family"], **initial})
        for arm in ("SELF", "CODE", "JEV"):
            event = ends.get(case["id"] + "-" + arm + "-P1")
            scored = score(event, case["checks"])
            answer = event["raw"].get("message", {}).get("content", "") if event else ""
            validation = validate(case["family"], case["prompt"], answer, bool(event and event["status"] == "complete"))
            decision = gate(validation, reviews.get(case["id"], []), require_reviews=arm == "JEV")
            rows.append({"case_id": case["id"], "family": case["family"], "arm": arm, "status": event["status"] if event else "missing",
                "initial_success": initial["success"], **scored, "runtime_valid": validation["valid"], "failed_runtime_checks": validation["failed_checks"],
                "gate": decision, "reviews": reviews.get(case["id"], []) if arm == "JEV" else []})
    totals = {}
    for arm in ("SELF", "CODE", "JEV"):
        selected = [r for r in rows if r["arm"] == arm]
        totals[arm] = {"success": sum(r["success"] for r in selected), "planned": len(selected),
            "repairs": sum(not r["initial_success"] and r["success"] for r in selected),
            "regressions": sum(r["initial_success"] and not r["success"] for r in selected),
            "incomplete": sum(r["status"] != "complete" for r in selected),
            "accepted": sum(r["gate"]["accepted"] for r in selected),
            "wrong_accepted": sum(r["gate"]["accepted"] and not r["success"] for r in selected),
            "correct_withheld": sum(not r["gate"]["accepted"] and r["success"] for r in selected)}
    result = {"created_at": stamp(), "scope": "Six reused development cases, P1 only, one shared initial and one correction per arm; no framing efficacy or population inference.",
              "initial_success": sum(r["success"] for r in initial_rows), "initial_planned": 6,
              "arms": totals, "initial_rows": initial_rows, "rows": rows,
              "runtime_keyed_disagreements": [f'{r["case_id"]}-{r["arm"]}' for r in rows if bool(r["success"]) != r["runtime_valid"]]}
    (out / "feedback-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("initial_success", "arms", "runtime_keyed_disagreements")}, indent=2))
    return result


def main() -> None:
    """Run explicit immutable stages, with no automatic terminal retry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--stage", choices=["freeze", "prepare", "collect", "finish", "analyze"], required=True)
    parser.add_argument("--server", default="jev")
    args = parser.parse_args()
    out = args.run.resolve()
    if args.stage == "freeze":
        freeze_mechanism(out)
    elif args.stage == "prepare":
        prepare(out, args.server)
    elif args.stage == "collect":
        collect(out)
    elif args.stage == "finish":
        freeze_mechanism(out)
        if len(read_ends(out / "corrections")) != 18:
            raise ValueError("Finish requires eighteen terminal correction cells")
        semantic_reviews(out, "final", args.server)
        analyze(out)
    else:
        freeze_mechanism(out)
        analyze(out)


if __name__ == "__main__":
    main()
