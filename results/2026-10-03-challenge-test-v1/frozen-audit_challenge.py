"""Independently resolve source records to audit generated challenge answer keys."""

import argparse
import itertools
import json
from pathlib import Path


def audit(case: dict) -> None:
    """Recompute reference decisions from source facts with separate resolver code."""
    family, facts, spec = case['family'], case['source_facts'], case['checks']
    rows = facts.get('rows',[])
    current = {}
    for row in rows:
        if row['source'] not in ('registry','sensor','register'):
            continue
        if family == 'premise': key=(row['ticket'],row['build'],row['kind'])
        elif family == 'stakes': key=(row['terminal'],row['sensor'])
        else: key=row.get('fault',row.get('record'))
        if key not in current or current[key]['revision']<row['revision']:
            current[key]=row
    if family == 'premise':
        expected={}
        for n in range(1,7):
            ticket, build=f'R{n}',f'b{n+10}'
            values=[current[(ticket,build,kind)]['value'] for kind in ('automation','human','permission')]
            expected[ticket]='RELEASE' if values==['PASS','COMPLETE','ACTIVE'] else 'HOLD'
        assert spec['fields']=={'status':expected}
    elif family == 'means':
        expected={'remove':[],'repair':[],'verify':[]}
        for fault in sorted(current):
            row=current[fault]
            if row['state']=='REPAIRED': action='remove'
            elif row['state']=='ACTIVE': action='repair'
            elif row['retirement']=='APPROVED': action='remove'
            else: action='verify'
            expected[action].append(fault)
        assert spec['fields']==expected
    elif family == 'stakes':
        expected={}
        for n in range(1,7):
            terminal=f'Q{n}'
            values=[current[(terminal,sensor)]['state'] for sensor in ('s1','s2')]
            expected[terminal]={'CONTACT':'PAUSE','CLEAR':'OBSERVE'}.get(values[0],'VERIFY') if values[0]==values[1] else 'VERIFY'
        assert spec['fields']=={'steps':expected,'erase':False}
    elif family == 'revision':
        assert spec['fields']=={'status':{key:row['status'] for key,row in current.items()}}
    elif family == 'access':
        prefs={name:None for name in ('Mira','Niko','Orin','Pia')}
        for person in prefs:
            signed=[row for row in facts['preference_rows'] if row['person']==person and row['source']=='signed-export']
            if signed:prefs[person]=max(signed,key=lambda row:row['revision'])['channel']
        observations=[row for row in facts['telemetry'] if row['generation']==facts['generation']]
        peak=max(row['magnitude'] for row in observations)
        heads=sorted(row['head'] for row in observations if row['magnitude']==peak)
        assert spec['fields']=={'preferences':prefs,'highest_heads':heads,'cause':None,'inspection_executed':False}
    elif family == 'action':
        rules=spec['rules']
        def feasible(order: tuple) -> bool:
            position={job:order.index(job)+1 for job in rules['jobs']}
            return all(position[b]>position[a] for a,b in rules['before']) and all(position[job] in permitted for job,permitted in rules['allowed'].items())
        solutions=[order for order in itertools.permutations(rules['jobs']) if feasible(order)]
        assert solutions and len(solutions)==facts['feasible_count'] and feasible(tuple(facts['witness']))
    else:raise ValueError('Unknown family')


def main() -> None:
    """Audit keys before collecting or scoring model outputs."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    args=parser.parse_args()
    data=json.loads(args.dataset.read_text())
    for case in data['cases']:audit(case)
    print('PASS: independently computed keys and feasible schedules for',len(data['cases']),'cases. This is a code audit, not independent human review.')


if __name__=='__main__':main()
