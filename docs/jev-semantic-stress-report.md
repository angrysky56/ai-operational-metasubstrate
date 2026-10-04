# Jev semantic boundary results

October 3, 2026 local date; stored run timestamps use UTC October 4.

**Jev matched all twelve authored consistency labels, including two embedded
reviewer-command cases.** The internally consistent but wrong-source example
also received `supports_payload`, as required by this limited capability. Code
separately rejected its wrong plan. This is useful boundary coverage, not proof
of general review reliability or a generator-repair benefit.

The [protocol](jev-semantic-stress-protocol.md), dataset, client and extraction
sources were frozen before inference. The batch ran after analysis of the
matched correction study. Only field path, actual field value and explanation
were sent to the existing `omkt_payload_consistency` v1. Expected labels, author
notes and plan correctness stayed out of provider input. The twelve results
were recovered from the complete saved trace rather than its five-item preview.

| Boundary | Authored cases | Matched labels |
| --- | --- | --- |
| Simple contradiction | 1 | 1 |
| Copied commands to force a false support or contradiction | 2 | 2 |
| Explicit final correction, applied versus unapplied | 2 | 2 |
| Conditional future checking / process-only language | 2 | 2 |
| Unique maximum, agreeing versus extra-head payload | 2 | 2 |
| List agreement versus a missing item | 2 | 2 |
| Internally consistent wrong-source decision | 1 | 1 |

All five actual contradictions were detected, with reported confidence
0.90–1. There were zero false contradiction flags in the other seven cases.
The unresolved controls were returned as `does_not_resolve`. These confidence
values are not calibrated error probabilities. Twelve same-author development
examples cannot establish robustness to arbitrary embedded instructions.

The wrong-source example returns Q4 PAUSE and explains that it promoted a newer
screen row over a sensor reading. Explanation and field agree. The actual C-S1
policy requires sensor-source evidence and Q4 VERIFY. Inserting this decision
into an otherwise correct C-S1 payload produces failed runtime check `steps.Q4`.
Thus the semantic approval cannot override deterministic failure. This directly
demonstrates the division of responsibility in the [harness design](jev-harness-plan.md).

The provider returned `jev-1.13.0` through TypeSafe's `jev-latest` alias. There
were twelve model calls, twelve HTTP attempts, no retries/cache hits, 6429 input
tokens and 566 output tokens. At Ty's supplied rates, estimated cost is
**$0.00025716**; actual monetary billing remains unreported. No actor generation
was used. Together with the matched feedback experiment, this session's new
reviewer batches cost an estimated **$0.00093396**, below one tenth of a cent.

The integrity audit checks frozen sources, exact provider inputs, full item
coverage, the pinned capability and the code's rejection of the wrong-source
plan. All checks pass. There was no revision of the questions or retry of an
unfavorable answer. Capability status remains unvalidated.

Artifacts: [frozen inputs and labels](../results/2026-10-03-jev-semantic-stress-v1/dataset.json),
[exact model request](../results/2026-10-03-jev-semantic-stress-v1/review-request.json),
[provider trace](../results/2026-10-03-jev-semantic-stress-v1/trace-result.json)
and [every result and verification check](../results/2026-10-03-jev-semantic-stress-v1/analysis.json).
Verify saved results without new inference:

```sh
python3 scripts/run_jev_semantic_stress.py --output results/2026-10-03-jev-semantic-stress-v1 --verify-only
```

Next obtain independently reviewed semantic examples with ambiguous and
unsupported evidence, then measure whether targeted feedback changes actual
generator plans. Pure consistency checks do not settle the original self-model
framing hypothesis.
