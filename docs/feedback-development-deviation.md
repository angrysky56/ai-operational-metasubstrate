# Feedback development: recorded retrieval defect

Recorded during correction collection, October 3, 2026. This note does not change
the frozen feedback mechanism, inputs or generation settings.

The twelve initial Jev judgments completed, but `run_capability` returned a
five-item preview with `moreResults: true`. The harness treated that preview as
the full batch. Its subsequently retrieved `get_run` trace contains all twelve
items. Only five judgments entered correction feedback: two for C-F1, two for
C-T1 and one for C-U1. C-G1, C-S1 and C-R1 received no semantic judgments.

Continue the original twenty-four actor attempts without changing feedback or
retrying terminal answers. Preserve its original extraction and analysis. This
run does not meet the intended complete-review protocol, and cannot establish
the incremental value of complete Jev feedback. The SELF/CODE conversations are
unaffected; all six starting plans were already correct under the independent
keyed grader and visible validator.

After original collection and analysis, repair extraction using every saved
trace item, requiring exact coverage, pinned reviewer identity, original item
data, provider questions and state. Test the actual twelve-item boundary,
missing/duplicate records and a remaining pagination cursor. A missing result
must stop preparation rather than silently remove feedback.

Save recovered reviews and recomputed final gate decisions in a separate
`coverage-repair` directory, with original artifact hashes and repair source
hashes. This requires no repeated actor or reviewer inference. Keep payload
scores unchanged. Recovered initial reviews are audit evidence only: they cannot
be retroactively added to conversations already generated. Report original and
repaired gate outcomes separately, and disclose the deviation in the report and
README. Use the repaired mechanism for any new run with a new source freeze.
