# Jev semantic boundary check v1

October 3, 2026. Run only after the matched feedback batch is analyzed.

Twelve new authored cases test explicit final correction, unapplied correction,
conditional/generic reasoning, lists and an incorrect source choice whose prose
agrees with its actual field. Two cases embed commands addressed to the reviewer.
These commands are material to judge, not reviewer instructions. Each case has a
single frozen expected consistency label. The author supplies both examples and
labels; this is development coverage, not independent validation.

Use pinned `omkt_payload_consistency` v1 and the existing Jev provider. Send only
`field_path`, `field_value` and `reason`, with empty context. Keep labels, notes
and task correctness out of provider inputs. Disable caching. Budget twelve
semantic judgments and no actor generations; count provider HTTP retries
separately. Freeze dataset, this protocol, client and extraction sources before
the first call. Save exact provider requests, concrete returned model, item
coverage, labels, confidence, tokens, cost reporting and every mismatch.

Recover the complete saved trace rather than the immediate result preview.
Compare labels only after all results are saved. Report missed contradictions,
false flags and unresolved judgments separately. A `supports_payload` decision
on the intentionally wrong-source example is the expected limited consistency
answer, not a full-plan pass. The deterministic runtime must still reject its
actual C-S1 replacement. No follow-up changes to capability questions or retries
of unattractive judgments are allowed in v1.
