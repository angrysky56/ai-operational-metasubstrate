"""Exercise exact fork construction and independent acceptance gates offline."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import feedback_harness as harness
from run_ollama import messages_for
from visible_plan_validator import gate, review_fields, validate

ROOT = Path(__file__).resolve().parents[1]


class FeedbackHarnessTests(unittest.TestCase):
    """Ensure the experiment forks identical initial state and keeps keys out."""

    def fixture(self, out: Path) -> dict:
        """Write synthetic terminal initial answers without model calls."""
        data = json.loads((ROOT / "data/challenge-dev-v1.json").read_text())
        cases = [c for c in data["cases"] if c["id"].endswith("1")]
        dataset = {"schema": 1, "conditions": {"P1": data["conditions"]["P1"]}, "cases": cases}
        (out / "initial-dataset.json").write_text(json.dumps(dataset))
        (out / "initial").mkdir()
        events = []
        for index, case in enumerate(cases, 1):
            spec = case["checks"]
            payload = spec["fields"] if spec["kind"] == "exact" else {"order": case["source_facts"]["witness"], "commit": False}
            cell = case["id"] + "-P1"
            events += [{"event": "started", "attempt": index, "cell": cell},
                       {"event": "finished", "attempt": index, "cell": cell, "status": "complete",
                        "raw": {"message": {"content": json.dumps(payload)}}, "elapsed_seconds": 1}]
        (out / "initial/events.jsonl").write_text("\n".join(json.dumps(e) for e in events))
        return dataset

    def test_shared_forks_equal_code_prefix_and_no_oracle_messages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            initial = self.fixture(out)
            with patch.object(harness, "mcp", return_value=harness.CAPABILITY):
                harness.prepare(out, "jev")
            frozen = json.loads((out / "correction-dataset.json").read_text())
            self.assertEqual(len(frozen["cases"]), 18)
            for source in initial["cases"]:
                variants = {c["feedback_arm"]: c for c in frozen["cases"] if c["origin_case"] == source["id"]}
                self.assertEqual(variants["SELF"]["history"], variants["CODE"]["history"])
                self.assertEqual(variants["CODE"]["history"], variants["JEV"]["history"])
                self.assertTrue(variants["JEV"]["prompt"].startswith(variants["CODE"]["prompt"]))
                for case in variants.values():
                    case["key"] = "SECRET_KEY_SENTINEL"
                    case["checks"] = {"SECRET_CHECK_SENTINEL": True}
                    messages = messages_for(frozen, {"case_id": case["id"], "condition": "P1"})
                    self.assertNotIn("SECRET_KEY_SENTINEL", json.dumps(messages))
                    self.assertNotIn("SECRET_CHECK_SENTINEL", json.dumps(messages))

    def test_unknown_confidence_or_label_cannot_pass_gate(self) -> None:
        case = next(c for c in json.loads((ROOT / "data/challenge-dev-v1.json").read_text())["cases"] if c["family"] == "revision")
        result = validate("revision", case["prompt"], json.dumps(case["checks"]["fields"] | {"reason": "Current register values apply."}))
        reviews = [{"field_path": item["field_path"], "candidate_sha256": result["candidate_sha256"],
                    "source_sha256": result["source_sha256"], "status": "complete", "choice": "supports_payload", "confidence": 0.9} for item in review_fields(result)]
        self.assertTrue(gate(result, reviews, True)["accepted"])
        reviews[0]["choice"] = "approve_everything"
        self.assertFalse(gate(result, reviews, True)["accepted"])
        reviews[0]["choice"] = "supports_payload"
        reviews[0]["confidence"] = float("nan")
        self.assertFalse(gate(result, reviews, True)["accepted"])

    def test_uncertain_mcp_started_marker_blocks_repeat_before_connection(self) -> None:
        """The SDK client's real preflight must refuse a previously started call."""
        import subprocess
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_file, output_file = root / "request.json", root / "response.json"
            input_file.write_text('{"name":"omkt_payload_consistency","version":1}')
            (root / "response.json.started.json").write_text('{}')
            result = subprocess.run(["node", str(ROOT / "harness/jev-client.ts"), "jev", "get_capability", str(input_file), str(output_file)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output_file.exists())
            self.assertIn("EEXIST", result.stderr)


if __name__ == "__main__":
    unittest.main()
