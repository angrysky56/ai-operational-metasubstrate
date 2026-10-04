"""Freeze and collect six shared starting answers for matched feedback development."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from run_ollama import stamp

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Keep shared initial collection independent of later runtime checks."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default="ornith-aq1.5:35b")
    parser.add_argument("--collect", action="store_true")
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    data = json.loads((ROOT / "data/challenge-dev-v1.json").read_text())
    selected = ["C-F1", "C-T1", "C-U1", "C-G1", "C-S1", "C-R1"]
    frozen = {"schema": 1, "stage": "matched_feedback_development_initial",
              "conditions": {"P1": data["conditions"]["P1"]},
              "cases": [next(c for c in data["cases"] if c["id"] == name) for name in selected]}
    blob = (json.dumps(frozen, indent=2) + "\n").encode()
    lock_path = out / "initial-input-lock.json"
    sources = ["scripts/prepare_feedback_initial.py", "scripts/run_ollama.py",
               "data/challenge-dev-v1.json", "docs/feedback-development-protocol.md"]
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in sources}
    if lock_path.exists():
        lock = json.loads(lock_path.read_text())
        if lock["source_hashes"] != hashes or (out / "initial-dataset.json").read_bytes() != blob:
            raise ValueError("Frozen initial inputs changed")
    else:
        (out / "initial-dataset.json").write_bytes(blob)
        for name in sources:
            (out / ("frozen-initial-" + Path(name).name)).write_bytes((ROOT / name).read_bytes())
        lock = {"created_at": stamp(), "source_hashes": hashes,
                "dataset_sha256": hashlib.sha256(blob).hexdigest(), "case_ids": selected}
        lock_path.write_text(json.dumps(lock, indent=2) + "\n")
    if args.collect:
        subprocess.run([sys.executable, str(ROOT / "scripts/run_ollama.py"), "--model", args.model,
                        "--output", str(out / "initial"), "--dataset", str(out / "initial-dataset.json"),
                        "--max-attempts", "6", "--limit-new", "6", "--max-seconds", "3600",
                        "--request-timeout", "900", "--num-ctx", "16384", "--num-predict", "8192",
                        "--think", "true", "--order-seed", "20261011"], check=True)


if __name__ == "__main__":
    main()
