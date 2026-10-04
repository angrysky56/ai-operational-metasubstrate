"""Verify request isolation, routing, budget accounting, and real resume behavior."""

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import run_ollama as runner


class RunnerTests(unittest.TestCase):
    """Use a controlled backend instead of spending model calls on infrastructure tests."""

    def test_routing_rejects_remote_alias(self) -> None:
        for model in (
            {"name": "local", "digest": "abc", "remote_host": "https://example.org"},
            {"name": "local", "digest": "abc", "remote_model": "other"},
            {"name": "model:cloud", "digest": "abc"},
        ):
            with self.assertRaises(ValueError):
                runner.local_model({"models": [model]}, model["name"])

    def test_key_and_family_never_reach_model(self) -> None:
        data = {"conditions": {"P0": "system"}, "cases": [{"id": "D1", "prompt": "visible", "key": "PRIVATE_KEY", "family": "SECRET_FAMILY"}]}
        messages = runner.messages_for(data, {"case_id": "D1", "condition": "P0"})
        self.assertEqual(messages, [{"role": "system", "content": "system"}, {"role": "user", "content": "visible"}])

    def test_uncertain_attempt_is_not_resubmitted(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unfinished"):
            runner.budget_state([{"event": "started", "attempt": 1, "cell": "D1-P0"}])

    def test_fixed_history_is_visible_but_metadata_is_not(self) -> None:
        history = [{"role": "user", "content": "initial", "key": "PRIVATE"}, {"role": "assistant", "content": "prior"}]
        data = {"conditions": {"P0": "system"}, "cases": [{"id": "R1", "prompt": "challenge", "history": history, "key": "SECRET"}]}
        messages = runner.messages_for(data, {"case_id": "R1", "condition": "P0"})
        self.assertEqual([m["role"] for m in messages], ["system", "user", "assistant", "user"])
        self.assertEqual(messages[1], {"role": "user", "content": "initial"})
        self.assertNotIn("PRIVATE", json.dumps(messages))
        data["cases"][0]["history"][0]["role"] = "system"
        with self.assertRaises(ValueError):
            runner.messages_for(data, {"case_id": "R1", "condition": "P0"})

    def test_finished_errors_consume_budget(self) -> None:
        events = [{"event": "started", "attempt": 1, "cell": "D1-P0"}, {"event": "finished", "attempt": 1, "cell": "D1-P0", "elapsed_seconds": 8, "status": "error"}]
        self.assertEqual(runner.budget_state(events), (1, 8, {"D1-P0"}))

    def test_truncation_and_thinking_only_are_not_answers(self) -> None:
        self.assertEqual(runner.response_status({"done": True, "done_reason": "length", "message": {"content": "partial"}}), "truncated")
        self.assertEqual(runner.response_status({"done": True, "message": {"content": "", "thinking": "reasoning"}}), "invalid")
        self.assertEqual(runner.response_status({"done": True, "message": {"content": "answer"}}), "complete")

    def test_resume_and_limit_use_actual_execution_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "results"
            dataset = Path(tmp) / "data.json"
            dataset.write_text(json.dumps({"schema": 1, "conditions": {"P0": "base", "P1": "guide", "P2": "self"}, "cases": [{"id": "D1", "prompt": "task", "key": "key"}]}))
            calls = []

            def fake_api(base: str, route: str, payload: dict | None = None, timeout: float = 10) -> dict:
                if route == "/api/tags":
                    return {"models": [{"name": "test", "digest": "fixed"}]}
                if route == "/api/show":
                    return {"capabilities": ["completion"]}
                if route == "/api/version":
                    return {"version": "test"}
                calls.append(payload)
                return {"done": True, "done_reason": "stop", "message": {"content": "answer"}, "eval_count": 2}

            argv = ["runner", "--model", "test", "--output", str(out), "--dataset", str(dataset), "--max-attempts", "2", "--limit-new", "1"]
            with patch.object(runner, "api", fake_api), patch.object(sys, "argv", argv), contextlib.redirect_stdout(io.StringIO()):
                runner.main()
                runner.main()
                runner.main()
            self.assertEqual(len(calls), 2)
            self.assertNotEqual(calls[0]["messages"], calls[1]["messages"])
            self.assertEqual(len(json.loads((out / "rating-packet.json").read_text())), 2)
            events = runner.read_events(out / "events.jsonl")
            self.assertEqual(runner.budget_state(events)[0], 2)
            dataset.write_text(dataset.read_text().replace('"task"', '"changed task"'))
            with patch.object(runner, "api", fake_api), patch.object(sys, "argv", argv), self.assertRaisesRegex(ValueError, "configuration changed"):
                runner.main()
            self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
