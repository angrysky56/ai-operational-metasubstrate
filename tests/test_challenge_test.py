"""Verify fresh instance generation and final-payload scoring boundaries."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_challenge import build
from build_challenge_test import build_test
from grade_challenge import grade
from analyze_challenge_test import analyze,final_payload,flags


class HoldoutTests(unittest.TestCase):
    """Check objective keys, corrections, and secondary-failure scopes."""

    def test_new_feasible_cases(self) -> None:
        cases=build_test();old={c['prompt'] for c in build()}
        self.assertEqual(len(cases),24)
        self.assertEqual(len({c['id'] for c in cases}),24)
        for case in cases:
            self.assertNotIn(case['prompt'],old)
            spec=case['checks']
            payload=spec['fields'] if spec['kind']=='exact' else {'order':case['source_facts']['witness'],'commit':False}
            self.assertEqual(grade(json.dumps(payload),spec)['success'],1)

    def test_corrected_final_object_is_accepted(self) -> None:
        payload,count=final_payload('{"status":{"K1":"FINAL"}}\nCorrected final:\n{"status":{"K1":"DRAFT"}}')
        self.assertEqual(count,2)
        self.assertEqual(payload,{'status':{'K1':'DRAFT'}})

    def test_secondary_flags_are_payload_scoped(self) -> None:
        case=next(c for c in build_test() if c['family']=='stakes')
        expected=case['checks']['fields']['steps']
        bad={key:('VERIFY' if value=='PAUSE' else 'PAUSE') for key,value in expected.items()}
        result=flags({'steps':bad,'erase':True},case)
        self.assertTrue(result['severe'])
        self.assertEqual(len(result['harmful_delay']),2)
        self.assertEqual(len(result['false_escalation']),4)
        self.assertFalse(flags(None,case)['severe'])
        self.assertEqual(flags(None,case)['harmful_delay'],[])

    def test_actual_analysis_path_keeps_incomplete_and_paired_harm(self) -> None:
        cases=build_test();order=[];events=[]
        damaged=next(c for c in cases if c['family']=='stakes')
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp)
            for case in cases:
                spec=case['checks']
                base=spec['fields'] if spec['kind']=='exact' else {'order':case['source_facts']['witness'],'commit':False}
                for condition in ('P0','P1','P2'):
                    cell=f"{case['id']}-{condition}"
                    order.append({'id':cell,'case_id':case['id'],'condition':condition})
                    payload=json.loads(json.dumps(base));status='complete'
                    if case['id']==damaged['id'] and condition=='P2':
                        urgent=next(key for key,value in payload['steps'].items() if value=='PAUSE')
                        payload['steps'][urgent]='VERIFY';payload['erase']=True
                    if case['id']==cases[0]['id'] and condition=='P0':status='truncated'
                    events.append({'event':'finished','cell':cell,'status':status,'raw':{'message':{'content':json.dumps(payload)}}})
            (run/'dataset.json').write_text(json.dumps({'cases':cases,'conditions':{'P0':'a','P1':'b','P2':'c'}}))
            (run/'manifest.json').write_text(json.dumps({'order':order}))
            (run/'events.jsonl').write_text('\n'.join(json.dumps(event) for event in events))
            result=analyze(run)
            self.assertEqual(result['conditions']['P0']['success'],23)
            self.assertEqual(result['conditions']['P0']['incomplete'],1)
            self.assertEqual(result['primary']['only_P1'],1)
            self.assertEqual(result['primary']['only_P2'],0)
            self.assertAlmostEqual(result['primary']['difference_pp'],-100/24)
            self.assertEqual(result['new_severe_P2_vs_P1'],[damaged['id']])
            self.assertEqual(len(result['new_delay_P2_vs_P1']),1)


if __name__=='__main__':unittest.main()
