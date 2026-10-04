# Matched feedback development results

October 3, 2026 local date; saved timestamps use UTC October 4.

**Ordinary guidance with thinking enabled produced six correct starting plans.
Self-checking, code feedback and code plus Jev each preserved all six.** There
were no errors to repair and no observed regressions. This batch demonstrates a
bounded correction workflow and correct-plan preservation, not incremental Jev
or OM-KT efficacy. A review-extraction defect also prevented complete Jev
feedback; its original evidence and a separately audited recovery are retained.

## What was compared

The [prospective development protocol](feedback-development-protocol.md) selected
C-F1, C-T1, C-U1, C-G1, C-S1 and C-R1: one reused public case per family. Only P1
ordinary guidance was used. This does not measure P0 baseline or P2 framing.

Each case received one initial generation. Its exact final-answer text and
original task history were forked into SELF, CODE and JEV conversations. Every
arm got exactly one correction, including initially correct cases. Separate
thinking text was recorded but not replayed. SELF received a generic recheck;
CODE added actual failed checks and authoritative visible records; JEV appended
narrow field/explanation reviews to byte-identical CODE feedback. The keyed
grader's expected maps were excluded from actor and reviewer messages.

All twenty-four actor calls used `ornith-aq1.5:35b`, digest
`3095dc99a4b4217ce6aa49a1d4d00aeb612b9361185d84eeb18fa013a70ca69d`, Ollama
0.34.4, thinking on, 16384 context, 8192 generation cap, temperature 0, seed 42,
top_k 20 and top_p 0.95. Initial and correction orders used seeds 20261011 and
20261012. Sources and exact inputs were frozen in stages before inspecting
new initial content or generating corrections. No terminal answer was retried.

## Complete-plan results

| Family / case | Shared initial | SELF | CODE | JEV |
| --- | --- | --- | --- | --- |
| Release gates / C-F1 | Correct | Correct | Correct | Correct |
| Access and telemetry / C-T1 | Correct | Correct | Correct | Correct |
| Schedule / C-U1 | Correct | Correct | Correct | Correct |
| Maintenance / C-G1 | Correct | Correct | Correct | Correct |
| Simulator protection / C-S1 | Correct | Correct | Correct | Correct |
| Register revision / C-R1 | Correct | Correct | Correct | Correct |
| Total | 6/6 | 6/6 | 6/6 | 6/6 |

All twenty-four calls completed with nonempty thinking and final-answer fields.
There were zero truncations, transport errors, repairs or regressions. Runtime
validation agreed with independent keyed correctness in all eighteen final
cells. This is six selected templates with shared starting answers, not eighteen
independent tasks or a population accuracy estimate.

The runtime derives its reference from visible records; evaluation uses the
separate frozen keys. They share low-level check predicates, so their agreement
cannot rule out a shared checker defect. There was no independent human review.

The earlier non-thinking challenge scores remain preserved. The separate P0
settings diagnostic improved two of three selected tasks with thinking and more
generation space; its simulator source error persisted. Here P1 handles all six,
including that simulator case. This is a useful setting/task feasibility result,
but guidance, settings and task selection prevent treating it as a controlled
effect estimate against the old studies.

## Review retrieval defect and recovery

Jev completed twelve initial and twelve final field judgments. Its immediate
`run_capability` response contained only five results and `moreResults: true`.
The original harness extracted those five, although its saved `get_run` trace
already contained all twelve. Initial feedback therefore included two judgments
for C-F1, two for C-T1, one for C-U1 and none for C-G1, C-S1 or C-R1. The
[deviation was recorded during collection](feedback-development-deviation.md).

The original final gate accepted two Jev plans and withheld four correct plans
for missing semantic coverage. This was a retrieval bug, not a Jev rejection.
After original analysis, complete saved judgments were recovered into a separate
directory without new model calls. All twelve final field judgments supported
their payloads, and the recovered gate accepted all six. The original missing
initial feedback remains a protocol deviation; it cannot be supplied retroactively.

| Gate | SELF accepted | CODE accepted | JEV accepted | Correct JEV plans withheld |
| --- | --- | --- | --- | --- |
| Original frozen extraction | 6/6 | 6/6 | 2/6 | 4/6 |
| Separate saved-review recovery | 6/6 | 6/6 | 6/6 | 0/6 |

Recovery changed no payload or correctness score. All twenty-four recovered
field judgments were `supports_payload`; reported confidence ranged 0.84–1.
These are selected internally consistent correct examples, not calibration or
contradiction-detection validation. Only two fields per candidate were reviewed.

Mechanism version 2 now consumes the complete persisted trace, requires every
requested ID, checks actual provider questions/state and refuses incomplete or
duplicate coverage. A second offline defect involved same-revision conflicting
records: rejection depended on row order if a newer row intervened. The validator
now checks conflicts across every authoritative revision before selecting the
latest row. Neither defect fix changes these stored payload scores. Original
sources remain in frozen snapshots; future runs require a new mechanism freeze.

## Time, tokens and cost

| Stage | Actor calls | Input tokens | Generated tokens, including thinking | Request time |
| --- | --- | --- | --- | --- |
| Shared initials | 6 | 7187 | 18476 | 524.95 s |
| SELF corrections | 6 | 9720 | 12000 | 329.93 s |
| CODE corrections | 6 | 11743 | 11503 | 324.24 s |
| JEV corrections | 6 | 12049 | 10826 | 324.19 s |
| Total | 24 | 40699 | 52805 | 1503.31 s, about 25 min |

Largest reported input-plus-generated total was 8448, below 16384. The simulator
initial used 7168 generated tokens, reinforcing the importance of thinking
headroom. Correction timing differences are descriptive single runs, not a
demonstrated speed benefit.

The twenty-four Jev judgments used 16920 input and 1104 output tokens, returned
`jev-1.13.0` via TypeSafe's configured `jev-latest` alias, and made twenty-four
HTTP attempts with no retries/cache hits. Billing was unreported. At Ty's quoted
$0.04/million input and $0/output, estimated reviewer cost is **$0.0006768**.
Local actor inference used the existing installation; no model download, Colab
session or paid generator was needed. The project added a small, pinned MCP SDK
client dependency with its own lockfile.

## Interpretation and next work

The fixture validator is useful independently of self-model framing. It derives
rules from supported visible policies, filters authority before revisions and
checks the actual submitted object. It supports six explicit fictional policy
templates; it is not a general policy interpreter or real-world execution system.

The immediate next research need is task difficulty under adequate reasoning
settings. Approximately 50% substantive baseline failure is a development target
that leaves room for improvement; it must not be manufactured by constraining
thinking, selecting held-out failures or dropping correct test instances. Develop
fresh cases, check family-level floors/ceilings, freeze settings, then freeze a
new test. Test P1/P2 under identical feedback access and actor budgets if studying
framing. Include actual initial failures before claiming a repair advantage.

For Jev's extra contribution, use separately reviewed semantic evidence tasks
where code cannot decide the relation by exact computation. The subsequent
[twelve-case semantic boundary check](jev-semantic-stress-report.md) tests narrow
review behavior and shows why consistency must remain separate from source truth.

## Evidence and reproduction

Thirty-seven code tests pass, including all thirty-six published visible-policy
cases, actual MCP preview/trace extraction, missing/stale reviews, altered
questions, uncertain request refusal and all six orders of conflicting records.
The completed-run audit passes integrity checks while explicitly recording
`protocol_complete: false`. Earlier study sources and the original DOCX hash
remain unchanged.

Artifacts: [original analysis](../results/2026-10-03-feedback-development/feedback-analysis.json),
[recovered gate analysis](../results/2026-10-03-feedback-development/coverage-repair/feedback-analysis.json),
[exact correction inputs](../results/2026-10-03-feedback-development/correction-dataset.json),
[initial actor log](../results/2026-10-03-feedback-development/initial/events.jsonl),
[correction actor log](../results/2026-10-03-feedback-development/corrections/events.jsonl),
[original source freeze](../results/2026-10-03-feedback-development/mechanism-lock.json),
[recovery freeze](../results/2026-10-03-feedback-development/coverage-repair/repair-lock.json)
and [verification](../results/2026-10-03-feedback-development/verification.json).

Recheck the stored experiment without any model requests:

```sh
python3 scripts/verify_feedback_development.py --run results/2026-10-03-feedback-development
```

This verifier is specific to the preserved v1 experiment and its documented
recovery. Current mechanism sources intentionally differ from its frozen v1
sources; do not resume that completed collection with the repaired implementation.
