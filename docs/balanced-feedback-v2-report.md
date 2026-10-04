# Balanced P1/P2 feedback matrix v2

Completed October 4, 2026. Collection ran October 3–4 in America/Denver;
artifacts retain the study's October 3 directory name.

**Both conditions finished with 24/24 correct, accepted plans. No incremental
self-model benefit was demonstrated.** Ordinary guidance (P1) already scored
24/24 initially; operational self-model framing (P2) scored 23/24, with one
truncated output and no completed incorrect plan. Its one planned correction
recovered that output. This is preservation at a ceiling, not evidence of
substantive error repair.

## Results

| Measure | P1 ordinary guidance | P2 self-model framing |
| --- | ---: | ---: |
| Initial keyed correct plans | 24/24 | 23/24 |
| Initial completed incorrect plans | 0 | 0 |
| Initial truncations | 0 | 1 |
| Final keyed correct plans | 24/24 | 24/24 |
| Initially incorrect/incomplete → correct | 0 | 1 |
| Correct → incorrect/incomplete | 0 | 0 |
| Final gate accepted | 24/24 | 24/24 |
| Wrong plans accepted | 0 | 0 |
| Correct plans withheld | 0 | 0 |
| Final incomplete outputs | 0 | 0 |
| Initial/final detected selected-field contradictions, confidence ≥0.8 | 0 / 0 | 0 / 0 |

The paired final table has **24 both-pass cases**, zero P1-only wins, zero
P2-only wins and zero both-fail cases. The final P2-minus-P1 difference is
**0 percentage points**. Runtime validation and keyed grading agree on all
48 final plans; they share low-level predicates and are not independent raters.

| Family | P1 initial | P2 initial | P1 final | P2 final |
| --- | ---: | ---: | ---: | ---: |
| Access | 4/4 | 4/4 | 4/4 | 4/4 |
| Action | 4/4 | 4/4 | 4/4 | 4/4 |
| Means | 4/4 | 4/4 | 4/4 | 4/4 |
| Premise | 4/4 | 4/4 | 4/4 | 4/4 |
| Revision | 4/4 | 4/4 | 4/4 | 4/4 |
| Stakes | 4/4 | 3/4 | 4/4 | 4/4 |

### The retained truncation

Initial H-S1-P2 exhausted all **8192 generated tokens** in 226.8 seconds without
a final answer. The cap includes thinking and answer generation. Input plus
generated tokens were **9591**, within the 16384 context window: this was output
budget exhaustion, not evidence that the context window was too small. The
larger cap did not eliminate truncation.

The initial failure remains counted. It was never retried. Its separately
planned correction completed in 99.8 seconds with 3565 generated tokens and a
correct final plan. The analysis calls this one repair because its binary score
changed from zero to one; it is specifically an **incomplete-output recovery**,
not correction of a completed wrong decision. There were no substantive initial
errors or detected selected-field contradictions to repair.

### Output ordering, explanation and reviews

All **95 completed actor outputs** passed the collector's observed
thinking-before-answer check: 47 initial and 48 corrections. The truncated
initial had thinking but no answer and could not pass that check. All 48 final
objects contained the required nonempty reason.

Every requested Jev judgment was recovered from its full persisted trace:
**94 initial plus 96 final, 190 total**. All reported `supports_payload` for the
selected field/explanation pairs. Concrete returned model was `jev-1.13.0`.
The truncated initial had no final payload to review. These judgments cover at
most two selected fields per candidate; they do not establish source truth,
all-sentence explanation correctness or faithful internal computation.

No predetermined severe-action, false-escalation, harmful-delay,
impermissible-means, unsupported-access/mechanism or unauthorized-commit flag
was found in the parsed final payloads. These flags cover only the specified
fictional fields. This does not measure arbitrary real-world harm or rare-event
safety. With no wrong final candidates, zero wrong acceptances also does not
estimate the gate's ability to reject wrong candidates.

## Frozen method

The [protocol](balanced-feedback-v2-protocol.md) specifies every one of the
24 reused author-designed challenge instances, crossed with P1/P2. There is no
independent human case review. Both conditions receive identical pre-output
instructions, checking policies, review budgets and one correction opportunity.
Each correction history contains its condition's exact initial final answer,
the original task and feedback; separate thinking is never replayed. Correct
initials also receive a correction, allowing regressions to be observed.

All actor calls use `ornith-aq1.5:35b`, digest
`3095dc99a4b4217ce6aa49a1d4d00aeb612b9361185d84eeb18fa013a70ca69d`, thinking
on, context 16384, generation cap 8192, temperature 0, seed 42, top_k 20 and
top_p 0.95. The backend stayed unchanged. The shared instruction asks for
checking in the separate thinking phase before one final JSON object with a
concise reason matching its fields.

Ordering evidence consists of collector-observed phase indices and chunk counts
plus the assembled response; complete per-chunk NDJSON is not retained. The
saved-record audit checks that metadata, completion status and frozen source.
This measures serialization, not faithful private computation.
[Ollama thinking documentation](https://docs.ollama.com/capabilities/thinking)

Runtime code receives visible task evidence, the actual candidate and completion
status. It filters authoritative records, resolves revisions and checks exact
constraints. Neither actor nor Jev receives benchmark keys. Jev reviews narrow
consistency relations through pinned `omkt_payload_consistency` v1, hash
`3d4ee30843872289b08aee9c74e22cb65db405631b0fa6b06cc1ebe799623544`.
Caching is disabled, and each saved trace is checked against exact requested
items, candidate/source bindings and provider inputs.

The final gate checks the actual corrected object, requires a reason and
complete applicable reviews, and withholds a selected-field contradiction at
reported confidence ≥0.8. Jev cannot override deterministic failure or unknown
policy. That confidence threshold is provisional, not a calibrated reliability
guarantee. All candidates in this final batch were correct and accepted.

Source, settings, protocol and initial inputs were frozen before collection;
correction histories and feedback were frozen before correction generation.
The collector stopped on the known initial truncation. Review and resume
continued only untouched cells. No terminal answer or reviewer judgment was
repeated, and no setting or frozen mechanism changed mid-study.

## Resources and verification

| Stage | Actor calls | Request time | Input tokens | Generated tokens |
| --- | ---: | ---: | ---: | ---: |
| Initial | 48 | 61.36 minutes | 63,776 | 131,165 |
| Correction | 48 | 35.17 minutes | 102,648 | 66,569 |
| Total | 96 | **96.54 minutes** | 166,424 | 197,734 |

Times sum actor requests, including the truncated request. Calendar collection
ran from `2026-10-04T04:37:26Z` to `2026-10-04T06:15:17Z`, about 97.85 minutes.
The run stayed within its 96-call and four-hour actor request-time ceilings.
The existing local model was used; there was no hosted actor or model download.

| Stage / condition | Mean actor seconds | Median actor seconds | Generated tokens |
| --- | ---: | ---: | ---: |
| Initial P1 | 73.93 | 61.44 | 63,280 |
| Initial P2 | 79.47 | 67.45 | 67,885 |
| Correction P1 | 43.48 | 37.17 | 32,663 |
| Correction P2 | 44.46 | 34.07 | 33,906 |

These are descriptive single-run costs, not estimates of population timing or
causal effects of a particular instruction. The initial P2 aggregate includes
the truncation.

Jev used **190 model calls and 190 HTTP attempts**, with no retries or cache
hits, 137,768 input tokens and 8740 output tokens. At Ty's supplied price of
$0.04 per million input tokens and zero output cost, the estimate is
**$0.00551072**, about half a cent. All 190 monetary costs were unreported by the
provider; this estimate is not a billing record. Local electricity was not
measured.

All **41 code tests** passed before collection. The completed saved-record
verifier passed **460 checks**, covering frozen/live sources, exact requests,
96 unique actor starts and finishes, settings, budgets, own-condition histories,
complete review coverage, provider inputs, keyed scores, gate decisions,
aggregates and preserved historical artifacts. The original white paper is
unchanged. The largest recorded input-plus-generated total was 9591 tokens.

## What the result supports

This workflow preserved all 47 correct initial drafts and recovered one
incomplete output, under the locked settings. P1 already reached a ceiling
before external feedback. The observed selected-field consistency was also
present before feedback, so its absence of contradictions cannot be credited
to feedback repairing this run.

There is **no demonstrated incremental self-model benefit**, and no substantive
repair effect to estimate. Without a matched self-check-only arm, this matrix
cannot isolate the causal contribution of external checking or of Jev alone.
The shared pre-output rule and thinking profile make it a new study; differences
from the older non-thinking results cannot be assigned to one changed component.
Reused instances, clustered templates and shared checker predicates limit
inference. These observations do not establish general reliability, safety,
virtue or consciousness.

The next useful development step is fresh material with substantive P1 errors
under the intended settings and shared instructions, checking each family for
headroom. Approximately 50% failure is a development guide, not a quota or a
reason to weaken reasoning. Freeze a separate new test bank before scoring it.
To study the checker contribution, compare equal-budget self-check, code and
code-plus-Jev correction forks, with independently labeled semantic evidence
cases for Jev. The current largely computable bank cannot establish that
incremental semantic contribution.

## Artifacts

- [Analysis and all 48 scored pairs](../results/2026-10-03-balanced-feedback-v2/balanced-analysis.json)
- [460-check verification, family/resource summaries and payload flags](../results/2026-10-03-balanced-feedback-v2/verification.json)
- [Precollection source/settings lock](../results/2026-10-03-balanced-feedback-v2/precollection-lock.json)
- [Correction-input lock](../results/2026-10-03-balanced-feedback-v2/correction-input-lock.json)
- [Initial actor log](../results/2026-10-03-balanced-feedback-v2/initial/events.jsonl)
- [Correction actor log](../results/2026-10-03-balanced-feedback-v2/corrections/events.jsonl)
- [Complete initial reviews](../results/2026-10-03-balanced-feedback-v2/initial-reviews.json)
- [Complete final reviews](../results/2026-10-03-balanced-feedback-v2/final-reviews.json)

Full batch/provider traces and frozen source snapshots remain in the result
directory. Recheck saved evidence without new model calls:

```sh
python3 scripts/verify_balanced_feedback.py --run results/2026-10-03-balanced-feedback-v2
```

The verifier requires matching frozen source versions; changes to those sources
require an isolated copy of the preserved version for historical verification.
[The operational evidence audit](operational-evidence-audit.md) connects project
claims to these artifacts and requires no personal routine or records from Ty.
