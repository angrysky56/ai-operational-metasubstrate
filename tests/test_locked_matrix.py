"""Verify locked settings, actual stream order and matched P1/P2 feedback."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_balanced_feedback as matrix
import run_locked_ollama as locked

ROOT = Path(__file__).resolve().parents[1]


class LockedMatrixTests(unittest.TestCase):
    """Use controlled stream records, never additional actor inference."""

    def test_thinking_before_answer_is_measured_and_late_thinking_rejected(self) -> None:
        thought = {"message": {"thinking": "check records"}, "done": False}
        answer = {"message": {"content": '{"status":{}}'}, "done": False}
        final = {"message": {}, "done": True, "done_reason": "stop", "eval_count": 9}
        good = locked.assemble_stream([thought, answer, final])
        self.assertEqual(locked.response_status(good), "complete")
        self.assertEqual(good["message"]["thinking"], "check records")
        for chunks in ([answer, thought, final], [thought, answer, thought, final],
                       [{"message": {"thinking": "x", "content": "y"}}, final], [answer, final]):
            self.assertEqual(locked.response_status(locked.assemble_stream(chunks)), "invalid")
        final["done_reason"] = "length"
        self.assertEqual(locked.response_status(locked.assemble_stream([thought, answer, final])), "truncated")

    def test_wrong_settings_rejected_before_any_network_call(self) -> None:
        for option in (["--think", "false"], ["--num-ctx", "4096"], ["--num-predict", "1024"], ["--seed", "7"]):
            with self.subTest(option=option), patch.object(locked, "api") as api:
                with patch.object(sys, "argv", ["locked", "--model", locked.settings_lock()["model"], "--output", "/tmp/not-created", *option]), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                    locked.main()
                api.assert_not_called()

    def test_pre_output_rule_identical_and_no_oracle_metadata_sent(self) -> None:
        data = {"conditions": {"P1": "ordinary", "P2": "framed"}, "cases": [{"id": "X", "prompt": "task", "key": "SECRET_KEY", "checks": {"SECRET_CHECK": True}}]}
        for condition in data["conditions"]:
            messages = locked.messages_for(data, {"case_id": "X", "condition": condition})
            self.assertTrue(messages[0]["content"].endswith(locked.pre_output_rule()))
            self.assertNotIn("SECRET", json.dumps(messages))

    def test_all_48_correction_histories_match_their_own_initial_condition(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            matrix.freeze(out)
            source = json.loads((out / "initial-dataset.json").read_text())
            (out / "initial").mkdir()
            events = []
            for case in source["cases"]:
                for condition in ("P1", "P2"):
                    attempt = len(events) // 2 + 1
                    payload = case["checks"]["fields"] if case["checks"]["kind"] == "exact" else {"order": case["source_facts"]["witness"], "commit": False}
                    payload = payload | {"reason": condition + " unique prior for " + case["id"]}
                    cell = case["id"] + "-" + condition
                    events += [{"event": "started", "attempt": attempt, "cell": cell}, {"event": "finished", "attempt": attempt,
                        "cell": cell, "status": "complete", "elapsed_seconds": 1, "raw": {"message": {"content": json.dumps(payload)}}}]
            (out / "initial/events.jsonl").write_text("\n".join(map(json.dumps, events)) + "\n")
            def fake_review(directory: Path, stage: str, server: str) -> dict:
                reviews = {e["cell"]: [] for e in events if e["event"] == "finished"}
                matrix.save(directory / "initial-reviews.json", {"by_pair": reviews})
                return reviews
            with patch.object(matrix, "mcp", return_value=matrix.CAPABILITY), patch.object(matrix, "review", side_effect=fake_review):
                matrix.prepare(out, "jev")
            correction = json.loads((out / "correction-dataset.json").read_text())
            self.assertEqual(len(correction["cases"]), 48)
            counts = {"P1": 0, "P2": 0}
            for case in correction["cases"]:
                condition = case["actor_condition"]
                self.assertEqual(case["conditions"], [condition])
                self.assertIn(condition + " unique prior for " + case["origin_case"], case["history"][-1]["content"])
                counts[condition] += 1
                case["key"] = "SECRET_KEY"
                case["checks"] = {"SECRET_CHECK": True}
                self.assertNotIn("SECRET", json.dumps(locked.messages_for(correction, {"case_id": case["id"], "condition": condition})))
            self.assertEqual(counts, {"P1": 24, "P2": 24})


if __name__ == "__main__":
    unittest.main()
