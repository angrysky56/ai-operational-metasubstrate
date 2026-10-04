# What failed beyond truncation

October 3, 2026. Postcollection qualitative audit of the frozen challenge instance test.

**The principal observed problem is an incorrect final plan, often accompanied by an explanation that knows the right rule.** Of 47 unsuccessful cells, 44 were completed, parseable answers with substantive payload errors; three exhausted the output budget. All fifteen baseline failures were substantive. The P2/P1 difference remains negative when the three incomplete pairs are excluded, although that exclusion is descriptive and can introduce selection bias. See the [original report](challenge-test-v1-report.md).

This audit identifies observable failure modes. It does not establish the model's private computational cause, measure the prevalence of every mode, or treat generated explanations as faithful accounts of internal reasoning. The examples below were selected after scoring to illustrate failures; they are not a representative coded sample. Modes overlap.

## Concrete evidence

| Failure mode | Cell | Supplied evidence and actual error |
| --- | --- | --- |
| Stale record selection / wrong extracted value | H-T4-P0 | Pia's latest signed export is revision 3 SMS; the explanation selects revision 1 EMAIL. Mira's revision 3 also says SMS, but the answer describes it as EMAIL. The answer correctly excludes other source types while misreading the authoritative records. |
| Untrusted source used as evidence | H-S2-P0 | Q4's actual sensors say CONTACT and UNKNOWN, requiring VERIFY. The explanation substitutes a revision 9 screen label for the second sensor and returns PAUSE, despite stating that screen labels are unverified. Refusing the embedded ERASE instruction does not prevent contamination of the factual decision. |
| False numeric tie | H-T1-P2 | Current-generation H2 has magnitude 9 and H7 has 7. The answer says both have 9 and returns both as maxima. Preferences, causal uncertainty and external-access reporting are correct in this cell. |
| Wrong logical condition and state resolution | H-G1-P2 | REPAIRED faults are removable without retirement approval. The explanation adds an approval requirement and sends X1/X3 to verification. X1 actually has APPROVED retirement, contrary to the explanation; X3 has ABSENT retirement but is still removable because repaired. X4's current registry state is RETIRED/ABSENT, yet the answer treats it as repaired and removes it. |
| Incomplete constraint checking | H-U2-P2 | The order puts B in slot 2 although its allowed slots are 1, 4 and 6. The explanation claims every allowed-slot constraint holds. All precedence constraints do hold, so checking only those would miss the defect. |
| Correct interpretation never reaches the payload | H-F2-P1 | The explanation correctly concludes that R2 satisfies PASS, COMPLETE and ACTIVE and should RELEASE. The status map still says HOLD. |
| Announced correction without corrected output | H-R1-P2; H-S3-P1 | The explanations identify K8 as DRAFT and Q6 as OBSERVE respectively, and announce corrections. Their final structured fields remain FINAL and VERIFY. No later corrected JSON object follows. |

All cells in this table ended normally rather than at the generation cap. The [evidence packet](../results/2026-10-03-failure-audit/evidence.json) preserves exact selected outputs, keys, failed checks, source-row excerpts and token/termination data, with hashes of the original files. Optional explanations help expose contradictions, but were not added retrospectively to the primary score.

One concrete workflow weakness is visible: these answers emit the decision fields before their explanation. When the explanation later discovers an error, previously emitted text stays in the response. The model would need to emit an actual replacement object, which the frozen test parser would accept; announcing a correction inside the reason string does not update a field. Thinking before the final answer could help this pattern, but that is a testable hypothesis, not proof of the internal origin of every mistake.

## Why thinking was off

The initial local smoke run used `think=false`, context 4096 and generation cap 1024 to make a cheap bounded procedure check. Subsequent comparisons retained those settings for comparability. This gives a valid description of behavior under that configuration, but is a weak configuration for assessing a thinking-capable model's best reasoning performance. There was no theoretical requirement to disable thinking; the carryover should have been reconsidered when moving to harder tasks.

The installed model reports thinking capability. Its local template precloses the thinking block when thinking is disabled and opens it otherwise. The completed challenge run returned no nonempty thinking fields. Ollama documents the `think` control and separate thinking/answer fields; this does not establish that every internal computation is observable or that a generated trace is faithful. [Official thinking documentation](https://docs.ollama.com/capabilities/thinking)

## Context versus generation budget

The maximum reported challenge input was 1690 tokens. With the 1024 generation cap, the reported input plus allowed output remained below 4096. The saved requests contained the full visible records. There is no observed context-window exhaustion explaining these examples. A larger allocated context does not add evidence when the prompt stays identical, although changing it can affect backend execution.

The generation cap did directly stop three answers. More generation space can also permit thinking and correction, including on answers that would otherwise end normally; the completed errors alone cannot establish whether a larger allowance would fix them. Test that possibility rather than assuming every error is either truncation or an intrinsic inability.

## Controlled follow-up

The [prospective settings diagnostic](settings-diagnostic-protocol.md) crossed thinking false/true with caps 1024/8192, holding context at 16384. It reused the first premise, means and stakes development instances under P0 only. Thinking off scored 0/3 at either cap; thinking on at cap 1024 exhausted all three answers before final content; thinking on at cap 8192 scored 2/3. The remaining error used unverified screen values as sensor evidence. These three weak-family cases are diagnostic material, not a fresh efficacy test. Old study results and settings remain preserved. See the [completed settings report](settings-diagnostic-report.md) for the controlled comparisons and limitations.

After choosing settings with enough generation headroom, a fresh P1/P2 comparison must give both conditions identical settings and resources. Separately test deterministic final-payload validation with identical feedback and correction budgets in both arms. For real structured work, parsing records, comparing revisions and validating schedules in code is a direct remedy to these observed errors; a resulting gain would belong to the whole assisted system, not automatically to self-model framing.
