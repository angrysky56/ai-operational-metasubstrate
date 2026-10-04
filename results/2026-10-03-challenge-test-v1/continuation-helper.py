"""Finish only unattempted cells; review known output-limit stops, never retry cells."""
import json
import subprocess
from datetime import datetime,timezone
from pathlib import Path
from scripts.run_ollama import read_events,budget_state

run=Path('results/2026-10-03-challenge-test-v1')
command=['python3','scripts/run_ollama.py','--model','ornith-aq1.5:35b','--dataset','data/challenge-test-v1.json','--output',str(run),'--max-attempts','72','--limit-new','72','--order-seed','20261008']
for invocation in range(73):
    events=read_events(run/'events.jsonl');attempts,spent,terminal=budget_state(events)
    if attempts>=72:
        print('Attempt ceiling reached; no replacements',flush=True);break
    if events and events[-1]['event']=='finished' and events[-1]['status']=='error':
        raise RuntimeError('Transport/backend error needs separate review; no retry')
    reason='Known output-budget truncation retained; resume unattempted cells only' if events and events[-1].get('status')=='truncated' else 'Continue unattempted cells under existing limits'
    review={'at':datetime.now(timezone.utc).isoformat(),'attempts_before':attempts,'request_seconds_before':spent,'decision':reason,'same_settings':True,'retry_terminal_cells':False}
    with (run/'continuation-reviews.jsonl').open('a') as stream:stream.write(json.dumps(review)+'\n')
    print(json.dumps(review),flush=True)
    with (run/'generation.log').open('a') as stream:result=subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT)
    if result.returncode:raise RuntimeError('Runner failed; inspect retained log')
    after=budget_state(read_events(run/'events.jsonl'))[0]
    if after<=attempts:
        print('No progress, possibly time budget exhausted; stopping',flush=True);break
else:raise RuntimeError('Invocation guard exhausted')
