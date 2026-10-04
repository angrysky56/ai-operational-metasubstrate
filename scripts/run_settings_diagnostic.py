"""Run a small, prospectively frozen local thinking/output-budget diagnostic.

Uses the existing checkpointed runner and graders. No retries, dependencies,
new prompt advice, validator feedback, or efficacy claims are introduced.
"""

import argparse
import hashlib
import json
import random
import subprocess
import sys
import time
from pathlib import Path

from analyze_challenge_test import final_payload
from grade_challenge import grade
from run_ollama import stamp

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    "scripts/run_settings_diagnostic.py", "scripts/run_ollama.py",
    "scripts/grade_challenge.py", "scripts/analyze_challenge_test.py",
    "data/challenge-dev-v1.json", "docs/settings-diagnostic-protocol.md",
]


def file_hash(path: Path) -> str:
    """Hash exact source bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare(out: Path) -> dict:
    """Freeze the first development instance from each of three weak families."""
    out.mkdir(parents=True, exist_ok=True)
    lock_path = out / "precollection-lock.json"
    if lock_path.exists():
        lock = json.loads(lock_path.read_text())
        for source, expected in lock["source_hashes"].items():
            if file_hash(ROOT / source) != expected:
                raise ValueError(f"Frozen source changed: {source}")
        if file_hash(out / "diagnostic-dataset.json") != lock["dataset_sha256"]:
            raise ValueError("Frozen diagnostic dataset changed")
        return lock
    data = json.loads((ROOT / "data/challenge-dev-v1.json").read_text())
    chosen = ["C-F1", "C-G1", "C-S1"]
    dataset = {"schema": 1, "stage": "exploratory_settings_diagnostic",
               "conditions": {"P0": data["conditions"]["P0"]},
               "cases": [next(c for c in data["cases"] if c["id"] == name) for name in chosen]}
    (out / "diagnostic-dataset.json").write_text(json.dumps(dataset, indent=2) + "\n")
    arms = [{"id": f"think-{str(think).lower()}-cap-{cap}", "think": think, "cap": cap}
            for think in (False, True) for cap in (1024, 8192)]
    random.Random(20261010).shuffle(arms)
    hashes = {source: file_hash(ROOT / source) for source in SOURCES}
    for source in SOURCES:
        (out / ("frozen-" + Path(source).name)).write_bytes((ROOT / source).read_bytes())
    lock = {"created_at": stamp(), "source_hashes": hashes,
            "dataset_sha256": file_hash(out / "diagnostic-dataset.json"),
            "arms": arms, "case_ids": chosen, "num_ctx": 16384,
            "case_order_seed": 20261010, "total_attempt_limit": 12,
            "request_timeout_seconds": 900, "wall_budget_seconds": 7200,
            "selection": "First development instance in premise, means and stakes; weak families selected after prior results. Not an efficacy sample."}
    lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    return lock


def finished(run: Path) -> list[dict]:
    """Read terminal checkpoints without altering them."""
    path = run / "events.jsonl"
    return [e for line in path.read_text().splitlines() if (e := json.loads(line))["event"] == "finished"] if path.exists() else []


def analyze(out: Path, lock: dict) -> dict:
    """Score completed final payloads only; keep missing/truncated cells as failures."""
    data = json.loads((out / "diagnostic-dataset.json").read_text())
    rows = []
    for arm in lock["arms"]:
        run = out / arm["id"]
        ends = finished(run)
        if len({e["cell"] for e in ends}) != len(ends):
            raise ValueError("Repeated cell")
        bycell = {e["cell"]: e for e in ends}
        for case in data["cases"]:
            event = bycell.get(case["id"] + "-P0")
            raw = event.get("raw", {}) if event else {}
            message = raw.get("message", {})
            score = {"success": 0, "error": "No complete final answer", "checks": []}
            if event and event["status"] == "complete":
                try:
                    payload, count = final_payload(message["content"])
                    score = grade(json.dumps(payload), case["checks"]) | {"object_count": count}
                except ValueError as error:
                    score["error"] = str(error)
            rows.append({"arm": arm["id"], "case_id": case["id"],
                         "status": event["status"] if event else "missing",
                         "elapsed_seconds": event["elapsed_seconds"] if event else None,
                         "prompt_tokens": raw.get("prompt_eval_count"),
                         "generated_tokens": raw.get("eval_count"),
                         "returned_thinking_characters": len(message.get("thinking", "")),
                         "answer_characters": len(message.get("content", "")), **score})
    result = {"created_at": stamp(), "scope": "Exploratory settings check, P0 only, three reused development instances, one generation per cell. No P2/P1 efficacy estimate.",
              "precollection_lock_sha256": file_hash(out / "precollection-lock.json"),
              "arms": {arm["id"]: {"success": sum(r["success"] for r in rows if r["arm"] == arm["id"]), "planned": 3,
                        "complete": sum(r["status"] == "complete" for r in rows if r["arm"] == arm["id"])} for arm in lock["arms"]},
              "rows": rows}
    (out / "settings-analysis.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    """Freeze, collect bounded requests sequentially, then save all planned scores."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="ornith-aq1.5:35b")
    parser.add_argument("--analyze-only", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    lock = prepare(out)
    started = time.monotonic()
    if not args.analyze_only:
        for arm in lock["arms"]:
            run = out / arm["id"]
            while len(finished(run)) < 3:
                if time.monotonic() - started > lock["wall_budget_seconds"] - 900:
                    raise RuntimeError("Diagnostic invocation wall budget reached")
                before = len(finished(run))
                subprocess.run([sys.executable, str(ROOT / "scripts/run_ollama.py"),
                    "--model", args.model, "--output", str(run),
                    "--dataset", str(out / "diagnostic-dataset.json"),
                    "--max-attempts", "3", "--limit-new", "3", "--max-seconds", "3600",
                    "--request-timeout", "900", "--num-ctx", "16384",
                    "--num-predict", str(arm["cap"]), "--think", str(arm["think"]).lower(),
                    "--order-seed", str(lock["case_order_seed"])], check=True)
                ends = finished(run)
                if len(ends) <= before or any(e["status"] not in ("complete", "truncated") for e in ends):
                    raise RuntimeError("Collection needs manual review; no uncertain/error retry")
                # Known truncations remain terminal; resume only untouched cells.
    result = analyze(out, lock)
    print(json.dumps(result["arms"], indent=2), flush=True)


if __name__ == "__main__":
    main()
