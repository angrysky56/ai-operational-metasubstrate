"""Recover saved review coverage and separately recompute submission gates.

Never regenerate a model answer or replace the original feedback and analysis.
The missing initial feedback remains a disclosed experimental deviation.
"""

import argparse
import copy
import hashlib
import json
from pathlib import Path

from jev_review_records import complete_reviews
from run_ollama import stamp
from visible_plan_validator import gate

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    """Hash retained source or artifact bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: dict) -> None:
    """Create an exact repair artifact without overwriting a prior result."""
    blob = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text() != blob:
        raise ValueError("Refusing to replace repair artifact: " + path.name)
    if not path.exists():
        path.write_text(blob)


def repair(run: Path) -> dict:
    """Recover twelve-item traces; change only final gate/review annotations."""
    out = run / "coverage-repair"
    out.mkdir(exist_ok=True)
    original = json.loads((run / "feedback-analysis.json").read_text())
    capability = json.loads((run / "mechanism-lock.json").read_text())["capability"]
    preserved = ["feedback-analysis.json", "mechanism-lock.json", "correction-input-lock.json",
                 "initial-dataset.json", "correction-dataset.json", "initial/events.jsonl", "corrections/events.jsonl"]
    for stage in ("initial", "final"):
        preserved += [stage + "-" + suffix + ".json" for suffix in
                      ("reviews", "review-request", "review-result", "review-bindings", "trace-result")]
    lock_path = out / "repair-lock.json"
    hashes = {name: sha(run / name) for name in preserved}
    sources = {name: sha(ROOT / name) for name in
               ("scripts/repair_feedback_coverage.py", "scripts/jev_review_records.py", "scripts/visible_plan_validator.py")}
    if lock_path.exists():
        lock = json.loads(lock_path.read_text())
        if lock["original_artifact_sha256"] != hashes or lock["repair_source_sha256"] != sources:
            raise ValueError("Original evidence or repair sources changed")
    else:
        lock = {"created_at": stamp(), "original_artifact_sha256": hashes, "repair_source_sha256": sources,
                "new_model_calls": 0, "scope": "Saved judgment recovery and final gate recomputation only; original feedback stays unchanged."}
        save(lock_path, lock)
    full = {}
    for stage in ("initial", "final"):
        request = json.loads((run / (stage + "-review-request.json")).read_text())
        bindings = json.loads((run / (stage + "-review-bindings.json")).read_text())["bindings"]
        trace = json.loads((run / (stage + "-trace-result.json")).read_text())["structuredContent"]["result"]
        full[stage] = complete_reviews(trace, request["items"], bindings, capability)
        save(out / (stage + "-reviews.json"), {"by_case": full[stage]})
    final_validations = json.loads((run / "final-review-bindings.json").read_text())["validations"]
    updated = copy.deepcopy(original)
    updated["created_at"] = lock["created_at"]
    updated["review_extraction_repair"] = lock["scope"]
    for row in updated["rows"]:
        if row["arm"] == "JEV":
            row["reviews"] = full["final"].get(row["case_id"], [])
            row["gate"] = gate(final_validations[row["case_id"]], row["reviews"], require_reviews=True)
    for arm, totals in updated["arms"].items():
        rows = [row for row in updated["rows"] if row["arm"] == arm]
        totals.update(accepted=sum(row["gate"]["accepted"] for row in rows),
                      wrong_accepted=sum(row["gate"]["accepted"] and not row["success"] for row in rows),
                      correct_withheld=sum(not row["gate"]["accepted"] and row["success"] for row in rows))
    save(out / "feedback-analysis.json", updated)
    return updated


def main() -> None:
    """Write separately preserved recovery without new model calls."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    updated = repair(args.run.resolve())
    print(json.dumps(updated["arms"], indent=2))


if __name__ == "__main__":
    main()
