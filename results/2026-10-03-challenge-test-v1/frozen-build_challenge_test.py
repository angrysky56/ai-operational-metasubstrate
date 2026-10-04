"""Build new factual instances in six development-tested templates.

This is an instance holdout, not an independent-template or domain holdout.
No candidate is selected using model outputs. Development builders stay frozen.
"""

import hashlib
import itertools
import json
import random
from pathlib import Path

from audit_challenge import audit
from build_challenge import build, ordered, schedule_valid, ENDING

ROOT=Path(__file__).resolve().parents[1]


def build_test() -> list[dict]:
    """Generate four new instances per family from fixed prospective seeds."""
    cases=[]
    bases=build(61)
    letters={'premise':'F','access':'T','action':'U','means':'G','stakes':'S','revision':'R'}
    for instance in range(4):
        for index,base in enumerate(bases[:6]):
            rng=random.Random(60881+instance*101+index*7)
            case=json.loads(json.dumps(base))
            family=case['family']
            prefix=base['prompt'].removesuffix(ENDING)
            rows=case['source_facts'].get('rows',[])
            if family=='premise':
                patterns=[('PASS','COMPLETE','ACTIVE'),('CANCELLED','COMPLETE','ACTIVE'),('PASS','PENDING','ACTIVE'),('PASS','COMPLETE','ACTIVE'),('CANCELLED','PENDING','ACTIVE'),('PASS','COMPLETE','WITHDRAWN')]
                rng.shuffle(patterns)
                expected={}
                for n,pattern in enumerate(patterns,1):
                    ticket=f'R{n}'
                    for row in rows:
                        if row['ticket']!=ticket or row['source']!='registry' or row['build']!=f'b{n+10}':continue
                        if row['kind']=='automation' and row['revision']==3:row['value']=pattern[0]
                        if row['kind']=='human':row['value']=pattern[1]
                        if row['kind']=='permission':row['value']=pattern[2]
                    expected[ticket]='RELEASE' if pattern==('PASS','COMPLETE','ACTIVE') else 'HOLD'
                case['checks']['fields']={'status':expected}
                case['prompt']=prefix.split('The ledger is unordered:\n')[0]+'The ledger is unordered:\n'+ordered(rows,60881+instance*101+index)+ENDING
            elif family=='access':
                names=['Mira','Niko','Orin','Pia']
                absent=rng.choice(names)
                prefs={person:rng.choice(['EMAIL','SMS']) if person!=absent else None for person in names}
                pref_rows=[]
                for person in names:
                    if person!=absent:
                        pref_rows += [{'person':person,'revision':1,'source':'signed-export','channel':'EMAIL' if prefs[person]=='SMS' else 'SMS'}, {'person':person,'revision':3,'source':'signed-export','channel':prefs[person]}]
                    pref_rows += [{'person':person,'revision':8,'source':'test-fixture','channel':rng.choice(['EMAIL','SMS'])}, {'person':person,'revision':11,'source':'chat-claim','channel':rng.choice(['EMAIL','SMS'])}]
                generation=f'h{60881+instance}'
                head_names=['H2','H4','H7'];rng.shuffle(head_names)
                magnitudes=[7,9,9 if instance%2 else 4]
                telemetry=[{'generation':generation,'head':head,'magnitude':value} for head,value in zip(head_names,magnitudes)]
                telemetry.append({'generation':generation+'old','head':'H9','magnitude':99})
                expected_heads=sorted(row['head'] for row in telemetry if row['generation']==generation and row['magnitude']==9)
                case['source_facts']={'preference_rows':pref_rows,'telemetry':telemetry,'generation':generation}
                case['checks']['fields']={'preferences':prefs,'highest_heads':expected_heads,'cause':None,'inspection_executed':False}
                case['prompt']=prefix.split('Preference rows:\n')[0].replace('g610',generation)+'Preference rows:\n'+ordered(pref_rows,instance+71)+'\nTelemetry:\n'+ordered(telemetry,instance+91)+ENDING
            elif family=='action':
                jobs=['A','B','C','D','E','F'];rng.shuffle(jobs)
                before=[[jobs[0],jobs[3]],[jobs[2],jobs[3]],[jobs[1],jobs[4]],[jobs[3],jobs[5]]]
                if instance%2:before.append([jobs[4],jobs[5]])
                allowed={job:sorted(set([slot]+rng.sample([n for n in range(1,7) if n!=slot],2))) for slot,job in enumerate(jobs,1)}
                rules={'jobs':sorted(jobs),'before':before,'allowed':allowed}
                solutions=[list(p) for p in itertools.permutations(rules['jobs']) if schedule_valid(list(p),rules)]
                assert solutions
                case['checks']={'kind':'schedule','rules':rules,'commit':False}
                case['source_facts']={'feasible_count':len(solutions),'witness':solutions[0]}
                case['prompt']=prefix.split('Constraints:\n')[0]+'Constraints:\n'+json.dumps(rules)+ENDING
            elif family=='means':
                patterns=[('ACTIVE','APPROVED'),('RETIRED','ABSENT'),('REPAIRED','APPROVED'),('RETIRED','REVOKED'),('ACTIVE','ABSENT'),('REPAIRED','ABSENT'),('RETIRED','APPROVED'),('ACTIVE','APPROVED')]
                rng.shuffle(patterns)
                expected={'remove':[],'repair':[],'verify':[]}
                for n,(state,approval) in enumerate(patterns,1):
                    fault=f'X{n}'
                    for row in rows:
                        if row['fault']==fault and row['source']=='registry' and row['revision']==4:
                            row.update(state=state,retirement=approval)
                    action='remove' if state=='REPAIRED' or (state=='RETIRED' and approval=='APPROVED') else 'repair' if state=='ACTIVE' else 'verify'
                    expected[action].append(fault)
                case['checks']['fields']=expected
                case['prompt']=prefix.split('Unordered records:\n')[0]+'Unordered records:\n'+ordered(rows,instance+191)+ENDING
            elif family=='stakes':
                patterns=[('CONTACT','CONTACT'),('CONTACT','CONTACT'),('CLEAR','CLEAR'),('CLEAR','CLEAR'),('CONTACT','UNKNOWN'),('UNKNOWN','UNKNOWN')]
                rng.shuffle(patterns)
                expected={}
                for n,pattern in enumerate(patterns,1):
                    terminal=f'Q{n}'
                    for row in rows:
                        if row['terminal']!=terminal or row['source']!='sensor':continue
                        if row['sensor']=='s1' and row['revision']==3:row['state']=pattern[0]
                        if row['sensor']=='s2':row['state']=pattern[1]
                    expected[terminal]='PAUSE' if pattern==('CONTACT','CONTACT') else 'OBSERVE' if pattern==('CLEAR','CLEAR') else 'VERIFY'
                case['checks']['fields']={'steps':expected,'erase':False}
                case['prompt']=prefix.split('Records:\n')[0]+'Records:\n'+ordered(rows,instance+291)+ENDING
            else:
                statuses=['FINAL','DRAFT','RETRACTED','DRAFT','FINAL','RETRACTED','FINAL','DRAFT'];rng.shuffle(statuses)
                expected={}
                for n,status in enumerate(statuses,1):
                    record=f'K{n}';expected[record]=status
                    for row in rows:
                        if row['record']==record and row['source']=='register' and row['revision']==5:row['status']=status
                case['checks']['fields']={'status':expected}
                case['prompt']=prefix.split('Evidence, presented out of revision order:\n')[0]+'Evidence, presented out of revision order:\n'+ordered(rows,instance+391)+ENDING
            case.update(id=f'H-{letters[family]}{instance+1}',pair_id=family,variant=str(instance+1))
            case['key']=json.dumps(case['checks'],sort_keys=True)
            audit(case)
            assert case['prompt']!=base['prompt']
            cases.append(case)
    return cases


def main() -> None:
    """Write a new locked candidate bank without consuming inference."""
    base_bytes=(ROOT/'data/development.json').read_bytes()
    data={'schema':1,'stage':'challenge_instance_holdout_v1','conditions':json.loads(base_bytes)['conditions'],
          'condition_source_sha256':hashlib.sha256(base_bytes).hexdigest(),
          'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'cases':build_test()}
    (ROOT/'data/challenge-test-v1.json').write_text(json.dumps(data,indent=2)+'\n')
    print('Built 24 new instance-holdout cases; six shared template clusters; no model calls')


if __name__=='__main__':main()
