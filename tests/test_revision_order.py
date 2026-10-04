"""Check that contradictory authoritative evidence cannot depend on row order."""

import itertools
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from visible_plan_validator import latest


class RevisionOrderTests(unittest.TestCase):
    """Exercise conflicting old rows as well as the selected current revision."""

    def test_conflicting_authoritative_revision_is_unresolved_in_every_order(self) -> None:
        rows = [
            {"source": "register", "record": "K1", "revision": 1, "status": "DRAFT"},
            {"source": "register", "record": "K1", "revision": 1, "status": "FINAL"},
            {"source": "register", "record": "K1", "revision": 2, "status": "RETRACTED"},
        ]
        for order in itertools.permutations(rows):
            with self.subTest(order=[row["status"] for row in order]):
                with self.assertRaisesRegex(ValueError, "Conflicting records"):
                    latest(list(order), "register", ("record",))


if __name__ == "__main__":
    unittest.main()
