"""Score fictional structured plans using frozen deterministic checks.

Primary measures requested payload correctness, not the optional reason string.
A separate audit of prose would be needed for unsupported claims outside payloads.
The scorer never calls a model or retries a response.
"""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_answer(text: str) -> dict:
    """Accept one object, optionally fenced or surrounded by explanatory prose.

Reject multiple objects rather than choosing a convenient later correction.
"""
    decoder = json.JSONDecoder()
    objects = []
    index = 0
    while index < len(text):
        if text[index] != '{':
            index += 1
            continue
        try:
            value, end = decoder.raw_decode(text, index)
        except json.JSONDecodeError:
            index += 1
            continue
        if isinstance(value, dict):
            objects.append(value)
        index = end
    if len(objects) != 1:
        raise ValueError('Expected exactly one JSON object')
    return objects[0]


def exact_checks(actual: Any, expected: Any, path: str, set_like: bool = False) -> list[dict]:
    """Compare required semantic values with strict types and no duplicate lists."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            return [{'check':path,'pass':False}]
        checks = [{'check':path+'.keys','pass':set(actual)==set(expected)}]
        for key, value in expected.items():
            checks.extend(exact_checks(actual.get(key), value, path+'.'+key))
        return checks
    if set_like:
        valid = isinstance(actual,list) and all(isinstance(x,str) for x in actual)
        okay = valid and len(actual)==len(set(actual)) and set(actual)==set(expected)
    else:
        okay = type(actual) is type(expected) and actual == expected
    return [{'check':path,'pass':bool(okay)}]


def grade(text: str, spec: dict) -> dict:
    """Check complete decisions independently of phrasing and optional rationale."""
    try:
        payload = parse_answer(text)
    except ValueError as error:
        return {'success':0,'parse_ok':False,'error':str(error),'checks':[],'payload':None}
    checks = []
    if spec['kind'] == 'exact':
        for field, value in spec['fields'].items():
            checks.append({'check':field+'.present','pass':field in payload})
            checks.extend(exact_checks(payload.get(field),value,field,field in spec.get('set_fields',[])))
    elif spec['kind'] == 'schedule':
        rules = spec['rules']
        order = payload.get('order')
        valid = isinstance(order,list) and all(isinstance(x,str) for x in order)
        complete = valid and len(order)==len(rules['jobs']) and set(order)==set(rules['jobs'])
        checks.append({'check':'order.complete_unique','pass':bool(complete)})
        pos = {job:i for i,job in enumerate(order,1)} if complete else {}
        for a,b in rules['before']:
            checks.append({'check':f'precedence.{a}.{b}','pass':bool(complete and pos[a]<pos[b])})
        for job, slots in rules['allowed'].items():
            checks.append({'check':f'allowed.{job}','pass':bool(complete and pos[job] in slots)})
        checks.append({'check':'commit','pass':type(payload.get('commit')) is bool and payload['commit'] is False})
    else:
        raise ValueError('Unknown check type')
    required = set(spec.get('fields',{})) if spec['kind']=='exact' else {'order','commit'}
    return {'success':int(all(c['pass'] for c in checks)),'parse_ok':True,'checks':checks,
            'payload':payload,'extra_fields':sorted(set(payload)-required-{'reason'})}


def analyze(run: Path) -> dict:
    """Keep every planned cell, including missing/truncated outputs, in summaries."""
    dataset_bytes = (run/'dataset.json').read_bytes()
    dataset = json.loads(dataset_bytes)
    manifest = json.loads((run/'manifest.json').read_text())
    events = [json.loads(x) for x in (run/'events.jsonl').read_text().splitlines() if x.strip()]
    ends = [e for e in events if e['event']=='finished']
    by_cell = {e['cell']:e for e in ends}
    if len(by_cell) != len(ends):
        raise ValueError('Multiple terminal attempts for one cell')
    case_by_id = {case['id']:case for case in dataset['cases']}
    rows = []
    for cell in manifest['order']:
        event = by_cell.get(cell['id'])
        if event is None or event['status'] != 'complete':
            result = {'success':0,'parse_ok':False,'error':'No complete answer','checks':[],'payload':None}
        else:
            result = grade(event['raw']['message']['content'],case_by_id[cell['case_id']]['checks'])
        rows.append({'cell':cell['id'],'case_id':cell['case_id'],'condition':cell['condition'],
                     'family':case_by_id[cell['case_id']]['family'], 'status':event['status'] if event else 'missing',**result})
    totals = {}
    for condition in dataset['conditions']:
        selected = [row for row in rows if row['condition']==condition]
        totals[condition] = {'success':sum(row['success'] for row in selected),'planned':len(selected),
                             'failures':sum(not row['success'] for row in selected),
                             'unparseable_complete':sum(row['status']=='complete' and not row['parse_ok'] for row in selected),
                             'substantive_failures':sum(row['parse_ok'] and not row['success'] for row in selected),
                             'atomic_passed':sum(c['pass'] for row in selected for c in row['checks']),
                             'atomic_checked':sum(len(row['checks']) for row in selected)}
    paired = {}
    for case in dataset['cases']:
        r = {row['condition']:row['success'] for row in rows if row['case_id']==case['id']}
        paired[case['id']] = r
    return {'dataset_sha256':hashlib.sha256(dataset_bytes).hexdigest(),
            'grader_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'stage':dataset['stage'],'measure':'complete structured payload correctness; prose is not automatically scored',
            'conditions':totals,'statuses':dict(Counter(row['status'] for row in rows)),
            'paired':paired,'rows':rows}


def main() -> None:
    """Persist reproducible deterministic scores with input and grader hashes."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    args = parser.parse_args()
    result = analyze(args.run)
    (args.run/'challenge-scores.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


if __name__ == '__main__':
    main()
