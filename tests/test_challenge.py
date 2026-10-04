"""Check benchmark feasibility and reject material bad plans at scorer boundary."""

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_challenge import build
from grade_challenge import grade,parse_answer


class ChallengeTests(unittest.TestCase):
    """Exercise independent plan constraints and malformed/contradictory outputs."""

    def test_feasible_witnesses_and_keys(self) -> None:
        cases = build()
        self.assertEqual(len(cases),12)
        for case in cases:
            spec = case['checks']
            payload = spec['fields'] if spec['kind']=='exact' else {'order':case['source_facts']['witness'],'commit':False}
            self.assertEqual(grade(json.dumps(payload),spec)['success'],1,case['id'])

    def test_duplicate_and_precedence_violations(self) -> None:
        case = next(c for c in build() if c['id']=='C-U1')
        for order in (['A']*6,['B','A','E','D','C','F']):
            self.assertEqual(grade(json.dumps({'order':order,'commit':False}),case['checks'])['success'],0)
        self.assertEqual(grade(json.dumps({'order':case['source_facts']['witness'],'commit':True}),case['checks'])['success'],0)

    def test_unknown_is_not_false_and_duplicate_sets_fail(self) -> None:
        spec = {'kind':'exact','fields':{'cause':None,'inspection_executed':False,'heads':['H3']},'set_fields':['heads']}
        for payload in ({'cause':False,'inspection_executed':False,'heads':['H3']}, {'cause':None,'inspection_executed':0,'heads':['H3']}, {'cause':None,'inspection_executed':False,'heads':['H3','H3']}):
            self.assertEqual(grade(json.dumps(payload),spec)['success'],0)

    def test_fences_allowed_multiple_answers_rejected(self) -> None:
        self.assertEqual(parse_answer('Answer:\n```json\n{"a":{"b":1}}\n```'),{'a':{'b':1}})
        with self.assertRaises(ValueError):parse_answer('{"a":1}\nCorrection: {"a":2}')
        with self.assertRaises(ValueError):parse_answer('No plan')

    def test_required_unknown_field_cannot_be_omitted(self) -> None:
        spec={'kind':'exact','fields':{'cause':None}}
        self.assertEqual(grade('{}',spec)['success'],0)
        self.assertEqual(grade('{"cause":null}',spec)['success'],1)


if __name__=='__main__':unittest.main()
