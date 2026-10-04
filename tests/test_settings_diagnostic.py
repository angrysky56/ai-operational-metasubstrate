"""Check diagnostic scoring without generating or interpreting model reasoning."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_settings_diagnostic import analyze


class SettingsDiagnosticTests(unittest.TestCase):
    """Retain incomplete cells and reject repeated terminal generations."""

    def fixture(self, root: Path) -> tuple[dict, list[dict]]:
        """Create three keyed cases and one synthetic arm."""
        cases = [{"id": f"C-{n}", "checks": {"kind": "exact", "fields": {"value": n}}} for n in range(3)]
        (root / "diagnostic-dataset.json").write_text(json.dumps({"cases": cases}))
        (root / "precollection-lock.json").write_text("{}")
        arm = root / "arm"
        arm.mkdir()
        events = [{"event": "finished", "cell": f"C-{n}-P0", "status": "complete", "elapsed_seconds": 1,
                   "raw": {"message": {"content": json.dumps({"value": n}), "thinking": "A proposed explanation"},
                           "eval_count": 100, "prompt_eval_count": 30}} for n in range(3)]
        return {"arms": [{"id": "arm"}]}, events

    def test_truncation_is_not_rescued_by_correct_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock, events = self.fixture(root)
            events[0]["status"] = "truncated"
            events[1]["raw"]["message"]["content"] = '{"value":0}\nCorrected:\n{"value":1}'
            (root / "arm/events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
            result = analyze(root, lock)
            self.assertEqual(result["arms"]["arm"]["success"], 2)
            self.assertEqual(result["arms"]["arm"]["planned"], 3)
            self.assertEqual(result["rows"][0]["success"], 0)
            self.assertEqual(result["rows"][1]["object_count"], 2)
            self.assertGreater(result["rows"][0]["returned_thinking_characters"], 0)

    def test_duplicate_terminal_cell_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            lock, events = self.fixture(root)
            events.append(events[0])
            (root / "arm/events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
            with self.assertRaisesRegex(ValueError, "Repeated cell"):
                analyze(root, lock)


if __name__ == "__main__":
    unittest.main()
