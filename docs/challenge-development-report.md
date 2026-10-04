# Challenge development v1 results

October 3, 2026 · Development only · Author-designed · Deterministic payload scoring

**The new development cases reached a moderate difficulty range:** baseline had five substantive failures out of twelve planned cases (41.7%), across premise, means and stakes. Including one multiple-payload response and one truncation, total baseline failure was seven of twelve (58.3%). This meets the frozen development criterion without counting those two non-substantive classifications toward the substantive target.

Exactly 50% failure is not required. The goal is understandable, relevant tasks that expose genuine mistakes and leave room for improvement and harm. This small, model-specific development result does not precisely estimate a population error rate and is not evidence of self-model efficacy. P2 was not run during development.

## Outcomes

| Measure | P0 minimal | P1 ordinary guidance |
| --- | --- | --- |
| Complete case success | 5/12 | 4/12 |
| Substantive payload failures | 5/12 | 8/12 |
| Completed but rejected multiple-object answer | 1/12 | 0/12 |
| Truncated answer | 1/12 | 0/12 |
| Diagnostic atomic checks passed, parsed answers only | 85/98 | 100/117 |

Whole-case success requires every requested entry or schedule constraint to be correct. Diagnostic checks are dependent and differ in count by task and parse availability; do not pool them as independent evidence or compare the two partial denominators as a treatment effect. The plan can be mostly correct and still fail overall.

| Family, two cases each | P0 successes | P1 successes |
| --- | --- | --- |
| Premise | 0/2 | 0/2 |
| Access | 2/2 | 1/2 |
| Action | 1/2 | 1/2 |
| Means | 0/2 | 0/2 |
| Stakes | 0/2 | 0/2 |
| Revision | 2/2 | 2/2 |

Ordinary guidance did not improve complete-plan performance in this development run. No conclusion about the self-model comparison follows. All cases and failures remain preserved; no wrong answer was retried.

## What failed

Release plans sometimes placed a genuinely qualified ticket on HOLD, even while their explanation recited its satisfied prerequisites. Another P1 answer incorrectly released a ticket whose authoritative human review remained pending. Several maintenance plans removed active faults or confused proposed dashboard changes with authoritative registry state.

Stakes plans mixed screen-source warning labels into the sensor evidence despite correctly repeating that screens were unverified. The prose and payload sometimes disagreed about which terminals should pause. An action plan violated an allowed slot while describing itself as feasible. These are substantive failures rather than a preference for longer or shorter writing.

One baseline maintenance response supplied an incorrect JSON plan and then a corrected second JSON plan. Under the development protocol's prospectively fixed one-object rule it was rejected as ambiguous; that response is not part of the five substantive-failure count. The subsequent test prospectively accepts the last complete object so successful correction can count. Original development ratings are not rewritten.

One baseline scheduling response exhausted the 1024-token cap while repeatedly revising an invalid plan. The invocation stopped. After review, the remaining unattempted cells were completed with identical settings; the truncated cell stayed recorded and was not regenerated. It counts as unsuccessful in the planned denominator, not as a scored complete payload.

## Integrity and cost

The same installed model, immutable digest, P0/P1 system text, inference settings, and local runner were used as pilot v1. Twenty-four attempts produced twenty-three complete responses and one truncation. Total request time was 311.08 seconds, about five minutes eleven seconds. No model download or paid inference was needed.

Keys were audited by separately written source-resolution code and schedule enumeration before generation. This cross-check is internal, not independent human review. During generation, **before any outputs were read or scores computed**, a checker bug was corrected: an omitted required top-level field whose expected value was null had been accepted. The corrected checker requires field presence as the protocol already specified. A regression test passed; the original and correction are preserved in the [correction record](../results/2026-10-03-challenge-dev-v1/grader-correction-before-scoring.json). Model inputs and answer keys did not change.

The [frozen protocol](challenge-development-protocol.md), [bank](../data/challenge-dev-v1.json), [full scores](../results/2026-10-03-challenge-dev-v1/challenge-scores.json), [raw outputs](../results/2026-10-03-challenge-dev-v1/events.jsonl), [manifest](../results/2026-10-03-challenge-dev-v1/manifest.json), and [precollection lock](../results/2026-10-03-challenge-dev-v1/precollection-lock.json) are available. Optional rationale was not automatically graded; additional unsupported prose claims may therefore escape these payload-only scores.

## Next step

Stop adapting this development bank. The [new 24-case instance test](challenge-test-v1-protocol.md) varies factual assignments and constraints within these six shared templates. It includes P0/P1/P2 and is frozen before its own collection. It is an instance holdout, not a new-domain or independently reviewed replication. Its baseline rate will be reported as observed, without replacing cases to achieve a desired 50%.
