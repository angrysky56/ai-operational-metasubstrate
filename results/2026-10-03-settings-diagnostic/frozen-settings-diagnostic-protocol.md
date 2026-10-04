# Thinking and output-budget diagnostic

October 3, 2026. Exploratory check following the completed adverse challenge result.

Question: do explicit thinking mode and a larger generation cap repair the observed record-resolution and final-plan failures on this installed model?

Use P0 alone with unchanged task text on C-F1, C-G1 and C-S1: the first development instance of each of the three weak premise, means and stakes families. Family selection is informed by previous results. These are reused development cases, not an independent test, a representative accuracy sample, or a P2/P1 comparison.

Cross thinking false/true with generation caps 1024/8192, holding context at 16384 in every arm. Keep model digest, temperature 0, seed 42, top_k 20 and top_p 0.95 fixed. Shuffle four arm blocks using seed 20261010; use the same seeded case order within blocks. Fresh conversations, one generation per cell, twelve attempts total. This small blocked run cannot separate every order effect or estimate sampling variability. A same-cap thinking toggle estimates the effect of the mode under that resource cap, not equal actual compute.

The larger context is headroom for extended generation. Original input counts did not exceed the 4096 context; this check does not separately estimate a context-size effect. Compare two caps within each mode and two modes within each cap; do not attribute the combined original-to-new settings change to one variable. Thinking may consume the generation allowance before a final answer appears; retain those exhausted cells as failures.

Use the existing frozen final-object parser and required-payload grader. Optional explanation/thinking is not scored. Complete answers ending normally are graded; truncated, missing, invalid or transport-error cells remain failures. Retain raw fields, input/generated counts, final payloads, returned thinking presence, and elapsed time. Never retry a terminal cell. Known length stops may resume only untouched cells. Stop on other errors or uncertain starts. Request timeout 900 seconds; per-arm cumulative request budget 3600 seconds; invocation wall budget 7200 seconds.

Freeze dataset, orchestration, runner, parser, grader and this protocol before calling the model. No prompt changes, feedback, downloads or paid inference. Preserve every original study artifact and score. A result here can motivate a prospective full comparison with enough thinking/output budget, but cannot reverse the earlier result or establish a general causal mechanism inside the model.

```sh
python3 scripts/run_settings_diagnostic.py --output results/2026-10-03-settings-diagnostic
```
