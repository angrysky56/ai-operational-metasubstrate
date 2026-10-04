"""Exercise the full saved-result boundary rather than a five-item preview."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from jev_review_records import complete_reviews
import feedback_harness as harness

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "results/2026-10-03-feedback-development"


class SavedReviewTests(unittest.TestCase):
    """Use the actual twelve-item MCP trace that exposed incomplete extraction."""

    def setUp(self) -> None:
        self.trace = json.loads((RUN / "initial-trace-result.json").read_text())["structuredContent"]["result"]
        self.request = json.loads((RUN / "initial-review-request.json").read_text())
        self.bindings = json.loads((RUN / "initial-review-bindings.json").read_text())["bindings"]
        self.capability = json.loads((RUN / "mechanism-lock.json").read_text())["capability"]

    def extract(self, trace: dict) -> dict:
        return complete_reviews(trace, self.request["items"], self.bindings, self.capability)

    def test_twelve_saved_judgments_survive_five_item_preview(self) -> None:
        preview = json.loads((RUN / "initial-review-result.json").read_text())["structuredContent"]["result"]
        self.assertEqual(len(preview["results"]), 5)
        self.assertTrue(preview["moreResults"])
        full = self.extract(self.trace)
        self.assertEqual(len(full), 6)
        self.assertTrue(all(len(rows) == 2 for rows in full.values()))
        self.assertEqual(sum(map(len, full.values())), 12)

    def test_harness_consumes_full_trace_at_real_mcp_boundary(self) -> None:
        """The live extraction path must use all records, not just its helper."""
        preview = json.loads((RUN / "initial-review-result.json").read_text())["structuredContent"]["result"]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "initial").mkdir()
            (out / "initial-dataset.json").write_bytes((RUN / "initial-dataset.json").read_bytes())
            (out / "initial/events.jsonl").write_bytes((RUN / "initial/events.jsonl").read_bytes())
            with patch.object(harness, "mcp", side_effect=[preview, self.trace]) as mcp:
                reviews = harness.semantic_reviews(out, "initial", "jev")
            self.assertEqual(mcp.call_count, 2)
            self.assertEqual(len(reviews), 6)
            self.assertTrue(all(len(rows) == 2 for rows in reviews.values()))

    def test_missing_duplicate_or_paginated_trace_cannot_approve(self) -> None:
        for change in ("missing", "duplicate", "cursor"):
            with self.subTest(change=change):
                trace = copy.deepcopy(self.trace)
                if change == "missing":
                    trace["items"].pop()
                elif change == "duplicate":
                    trace["items"].append(trace["items"][0])
                else:
                    trace["nextCursor"] = "remaining-page"
                with self.assertRaises(ValueError):
                    self.extract(trace)

    def test_changed_question_state_or_identity_cannot_approve(self) -> None:
        for change in ("question", "state", "identity"):
            with self.subTest(change=change):
                trace = copy.deepcopy(self.trace)
                if change == "question":
                    trace["items"][0]["events"][0]["request"]["questions"] = {}
                elif change == "state":
                    trace["items"][0]["events"][0]["request"]["state"]["context"] = {"expected": "injected"}
                else:
                    trace["manifest"]["capability"]["hash"] = "changed"
                with self.assertRaises(ValueError):
                    self.extract(trace)


if __name__ == "__main__":
    unittest.main()
