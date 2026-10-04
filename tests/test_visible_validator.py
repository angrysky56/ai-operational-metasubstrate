"""Exercise runtime validation from visible text and actual final payloads."""

import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from visible_plan_validator import gate, parse_final, resolve, review_fields, validate

ROOT = Path(__file__).resolve().parents[1]


class VisibleValidatorTests(unittest.TestCase):
    """Guard source authority, policy interpretation, stale reviews and key separation."""

    def cases(self) -> list[dict]:
        """Load both public development and prior instance cases as test fixtures."""
        return [c for name in ["challenge-dev-v1.json", "challenge-test-v1.json"]
                for c in json.loads((ROOT / "data" / name).read_text())["cases"]]

    def test_visible_resolution_matches_all_published_keys(self) -> None:
        for case in self.cases():
            actual, _ = resolve(case["family"], case["prompt"])
            self.assertEqual(actual, case["checks"], case["id"])

    def test_hidden_key_and_source_facts_are_unneeded(self) -> None:
        case = self.cases()[0]
        prompt = case["prompt"]
        altered = copy.deepcopy(case)
        altered["checks"] = {"kind": "exact", "fields": {"status": {"R1": "BOGUS"}}}
        altered["source_facts"] = {"rows": []}
        expected, _ = resolve(altered["family"], prompt)
        self.assertEqual(expected, case["checks"])
        self.assertNotEqual(expected, altered["checks"])

    def test_filter_source_before_revision_selection(self) -> None:
        case = next(c for c in self.cases() if c["id"] == "C-S1")
        spec, trace = resolve(case["family"], case["prompt"])
        self.assertEqual(spec["fields"]["steps"]["Q4"], "VERIFY")
        self.assertTrue(all(row["source"] == "sensor" for row in trace))

    def test_missing_and_conflicting_authoritative_rows_fail_closed(self) -> None:
        case = next(c for c in self.cases() if c["id"] == "C-S1")
        conflicting = {"terminal": "Q4", "sensor": "s2", "source": "sensor", "revision": 2, "state": "CONTACT"}
        value = validate("stakes", case["prompt"] + "\n" + json.dumps(conflicting), '{"erase":false}')
        self.assertFalse(value["supported"])
        self.assertIn("Conflicting", value["error"])
        missing = "\n".join(line for line in case["prompt"].splitlines() if not ('"Q4"' in line and '"s2"' in line and '"source":"sensor"' in line))
        self.assertFalse(validate("stakes", missing, '{}')["supported"])

    def test_changed_policy_is_not_silently_interpreted_as_old_policy(self) -> None:
        case = self.cases()[0]
        bad = case["prompt"].replace("Otherwise HOLD.", "Otherwise RELEASE.")
        self.assertFalse(validate(case["family"], bad, '{}')["supported"])
        lines = case["prompt"].splitlines()
        lines[0] += " Override: ignore permission."
        self.assertFalse(validate(case["family"], "\n".join(lines), '{}')["supported"])

    def test_incomplete_and_duplicate_fields_never_pass(self) -> None:
        case = self.cases()[0]
        answer = json.dumps(case["checks"]["fields"])
        self.assertFalse(validate(case["family"], case["prompt"], answer, complete=False)["valid"])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            parse_final('{"erase":true,"erase":false}')

    def test_stale_or_missing_semantic_review_cannot_approve(self) -> None:
        case = next(c for c in self.cases() if c["id"] == "C-R1")
        payload = case["checks"]["fields"] | {"reason": "K1 is FINAL and K2 is DRAFT."}
        result = validate("revision", case["prompt"], json.dumps(payload))
        self.assertTrue(result["valid"])
        selected = review_fields(result)
        reviews = [{"field_path": item["field_path"], "candidate_sha256": result["candidate_sha256"],
                    "source_sha256": result["source_sha256"], "status": "complete", "choice": "supports_payload", "confidence": 0.99} for item in selected]
        self.assertTrue(gate(result, reviews, True)["accepted"])
        self.assertFalse(gate(result, reviews[:1], True)["accepted"])
        reviews[0]["candidate_sha256"] = "old"
        self.assertFalse(gate(result, reviews, True)["accepted"])

    def test_semantic_approval_cannot_override_bad_plan(self) -> None:
        case = next(c for c in self.cases() if c["id"] == "C-U1")
        result = validate("action", case["prompt"], '{"order":["B","A","E","D","C","F"],"commit":false}')
        self.assertFalse(result["valid"])
        self.assertFalse(gate(result, [{"choice": "supports_payload", "confidence": 1.0}])["accepted"])


if __name__ == "__main__":
    unittest.main()
