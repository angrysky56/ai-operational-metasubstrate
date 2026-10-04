"""Verify frozen inputs and exact requests for the completed local diagnostic."""

import argparse
import hashlib
import json
from pathlib import Path

from run_ollama import messages_for, stamp

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    """Hash exact bytes without changing the artifact."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(run: Path) -> dict:
    """Check all twelve cells and the sources needed to reproduce their scores."""
    lock = json.loads((run / "precollection-lock.json").read_text())
    data = json.loads((run / "diagnostic-dataset.json").read_text())
    checks = {"dataset_hash": sha(run / "diagnostic-dataset.json") == lock["dataset_sha256"]}
    for source, expected in lock["source_hashes"].items():
        checks["live_source:" + source] = sha(ROOT / source) == expected
        checks["frozen_source:" + source] = sha(run / ("frozen-" + Path(source).name)) == expected
    model_digests, backends, all_ends, answers = set(), set(), [], {}
    for arm in lock["arms"]:
        directory = run / arm["id"]
        manifest = json.loads((directory / "manifest.json").read_text())
        config = manifest["config"]
        model_digests.add(config["digest"])
        backends.add(json.dumps(config["backend"], sort_keys=True))
        options = {"temperature": 0, "seed": 42, "num_predict": arm["cap"],
                   "num_ctx": 16384, "top_k": 20, "top_p": 0.95}
        checks[arm["id"] + ":settings"] = config["options"] == options and config["think"] is arm["think"]
        checks[arm["id"] + ":dataset"] = sha(directory / "dataset.json") == lock["dataset_sha256"]
        events = [json.loads(line) for line in (directory / "events.jsonl").read_text().splitlines()]
        starts = [e for e in events if e["event"] == "started"]
        ends = [e for e in events if e["event"] == "finished"]
        checks[arm["id"] + ":accounting"] = (
            len(starts) == len(ends) == 3
            and len({e["cell"] for e in starts}) == 3
            and {e["attempt"] for e in starts} == {e["attempt"] for e in ends}
            and {e["cell"] for e in ends} == {c["id"] + "-P0" for c in data["cases"]}
        )
        bycell = {c["id"]: c for c in manifest["order"]}
        checks[arm["id"] + ":exact_visible_inputs"] = all(
            e["request"]["messages"] == messages_for(data, bycell[e["cell"]])
            and e["request"]["options"] == options
            and e["request"]["think"] is arm["think"] for e in starts
        )
        all_ends.extend(ends)
        answers[arm["id"]] = {e["cell"]: e["raw"].get("message", {}).get("content", "") for e in ends}
    checks["identical_model_digest"] = len(model_digests) == 1
    checks["identical_backend"] = len(backends) == 1
    checks["twelve_terminal_attempts"] = len(all_ends) == 12
    evidence = json.loads((ROOT / "results/2026-10-03-failure-audit/evidence.json").read_text())
    checks["original_test_sources_preserved"] = all(sha(ROOT / source) == expected for source, expected in evidence["source_hashes"].items())
    result = {"created_at": stamp(), "all_pass": all(checks.values()), "checks": checks,
              "thinking_off_answers_identical_at_two_caps": answers["think-false-cap-1024"] == answers["think-false-cap-8192"],
              "total_request_seconds": sum(e["elapsed_seconds"] for e in all_ends),
              "generated_tokens": sum(e["raw"].get("eval_count", 0) for e in all_ends),
              "source_sha256": sha(Path(__file__)),
              "analysis_sha256": sha(run / "settings-analysis.json")}
    (run / "verification.json").write_text(json.dumps(result, indent=2) + "\n")
    if not result["all_pass"]:
        raise ValueError("Diagnostic verification failed")
    return result


def main() -> None:
    """Save reproducible verification without generating new responses."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.run.resolve()), indent=2))


if __name__ == "__main__":
    main()
