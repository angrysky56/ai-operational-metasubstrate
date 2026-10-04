"""Freeze the published development prompts and keys into portable JSON."""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Extract only the four prompt blocks and six marked development fixtures."""
    source = ROOT / "docs/prompt-protocol.md"
    text = source.read_text()
    blocks = re.findall(r"```text\n(.*?)\n```", text, re.S)
    if len(blocks) != 4:
        raise ValueError("Expected exactly four protocol blocks")
    cases = []
    parts = re.split(r"\n### (D\d): ([^\n]+)\n", text)[1:]
    for index in range(0, len(parts), 3):
        case_id, family, section = parts[index:index + 3]
        prompt = re.search(r"\*\*Visible task:\*\*\n\n> ([^\n]+)", section)
        key = re.search(r"\*\*Key:\*\* ([^\n]+)", section)
        if prompt is None or key is None:
            raise ValueError(f"Missing prompt or key in {case_id}")
        cases.append({"id": case_id, "family": family, "prompt": prompt[1], "key": key[1]})
    if len(cases) != 6:
        raise ValueError("Expected six development cases")
    baseline, common, checklist, self_model = blocks
    payload = {
        "schema": 1,
        "stage": "development_smoke_only",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "conditions": {
            "P0": baseline,
            "P1": "\n\n".join((baseline, common, checklist)),
            "P2": "\n\n".join((baseline, common, self_model)),
        },
        "cases": cases,
    }
    target = ROOT / "data/development.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print(f"Frozen {len(cases)} development cases and three conditions")


if __name__ == "__main__":
    main()
