"""Check pairing and cluster resampling against known outcomes."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from analyze_pilot import bootstrap_range, paired_summary


class AnalysisTests(unittest.TestCase):
    """Detect reversed comparisons and broken dependence preservation."""

    def test_paired_table(self) -> None:
        outcomes = [(1, 1), (1, 0), (0, 1), (0, 0)]
        scores = {(str(i), p): {"success": value} for i, pair in enumerate(outcomes) for p, value in zip(("P2", "P1"), pair)}
        self.assertEqual(paired_summary(scores, list(map(str, range(4)))), {"both_success": 1, "only_P2": 1, "only_P1": 1, "neither": 1, "difference_pp": 0})

    def test_within_pair_offsets_remain_together(self) -> None:
        cases = [{"id": str(i), "pair_id": str(i // 2)} for i in range(4)]
        scores = {(str(i), p): {"success": value} for i in range(4) for p, value in (("P2", i % 2), ("P1", 1 - i % 2))}
        self.assertEqual(bootstrap_range(scores, cases, samples=100), [0, 0])

    def test_positive_direction(self) -> None:
        cases = [{"id": "a", "pair_id": "one"}, {"id": "b", "pair_id": "one"}]
        scores = {(c["id"], p): {"success": int(p == "P2")} for c in cases for p in ("P2", "P1")}
        self.assertEqual(bootstrap_range(scores, cases, samples=100), [100, 100])


if __name__ == "__main__":
    unittest.main()
