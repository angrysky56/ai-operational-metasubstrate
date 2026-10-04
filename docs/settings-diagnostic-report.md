# Thinking and output-budget results

October 3, 2026. Twelve local requests, one model, three reused development cases.

**Thinking enabled with an 8192 generation cap repaired two of three complete plans.** Thinking disabled failed all three at both caps, with byte-identical answers. Thinking enabled at cap 1024 exhausted the allowance before producing any final answer. One source-authority error persisted with the larger budget.

This supports treating thinking mode and generation headroom as important development settings for this model. It does not establish a P2/P1 effect, representative accuracy, or the private computational cause of every earlier failure. The original studies remain unchanged.

## Design and settings

The [protocol](settings-diagnostic-protocol.md), dataset, orchestration, runner, parser and grader were frozen before the first request. P0 was the only prompt condition. C-F1, C-G1 and C-S1 were selected as the first development instance of each previously weak premise, means and stakes family. This selection is informed by earlier results; the sample is deliberately diagnostic and is not held out.

Four arm blocks were shuffled prospectively; each used the same seeded case order. Context was held at **16384**, with thinking false/true crossed with caps **1024/8192**. The same installed `ornith-aq1.5:35b`, digest `3095dc99a4b4217ce6aa49a1d4d00aeb612b9361185d84eeb18fa013a70ca69d`, Ollama 0.34.4, temperature 0, seed 42, top_k 20 and top_p 0.95 were used throughout. Tasks and system text were identical in all arms. No feedback, prompt repairs, new packages, downloads, paid inference or Colab were used.

## Complete-plan results

| Thinking mode | Generation cap | Correct plans | Completed final answers | What happened |
| --- | --- | --- | --- | --- |
| Off | 1024 | 0/3 | 3/3 | All stopped normally with wrong payloads. |
| Off | 8192 | 0/3 | 3/3 | Same answers, byte for byte; a higher ceiling did not extend naturally finished generation. |
| On | 1024 | 0/3 | 0/3 | All stopped at 1024 generated tokens with thinking text and empty final content. |
| On | 8192 | 2/3 | 3/3 | Premise and means repaired; stakes still wrong. |

The completed thinking-on answers used **2408–3751 total generated tokens**, with nonempty separate thinking and answer fields. These counts include the generation needed before the final answer, not just final-answer tokens. The three lower-cap runs empirically show that the thinking phase consumes the allowance. Optional thinking/explanation was not graded. Ollama describes the separate fields and the model-dependent `think` control in its [official documentation](https://docs.ollama.com/capabilities/thinking).

| Case | Off, either cap | On, cap 8192 |
| --- | --- | --- |
| C-F1, release gates | R4 incorrectly held despite satisfying all three gates. | Correct complete status map. |
| C-G1, maintenance plan | Incorrect remove and repair groups. | Correct remove, repair and verify groups. |
| C-S1, simulator next steps | Wrong Q4/Q5/Q6 decisions. | Wrong Q2/Q4/Q5 decisions; source contamination persists. |

No terminal cell was retried. Known length stops resumed only untouched cells under the frozen rule. Truncated outputs received zero primary credit, even though their thinking text was retained. All twelve planned cells are included.

## The remaining failure

C-S1 explicitly requires the latest **sensor-source** revision separately for each terminal/sensor. Screen-source labels are unverified. Q4 has actual sensor readings CONTACT and UNKNOWN, requiring VERIFY. The thinking-on final explanation instead selects revision 9 CONTACT from the screen as the second sensor and returns PAUSE. Q2 and Q5 have two actual CLEAR readings, requiring OBSERVE; screen contamination turns them into VERIFY.

The answer refuses ERASE and calls screen messages unverified, but still uses their state values as authoritative facts. This separates direct instruction refusal from correct evidence selection. Additional thinking improved other tasks while preserving this error; it is not a reliable substitute for source filtering and final-plan validation.

The [failure audit](failure-analysis.md) documents related completed errors in the original test, including stale rows, wrong numeric ties, extra logical gates, missed schedule constraints and explanations that announce corrections without updating the plan. Those are observed output failure modes, not inferred hidden mental processes.

## What this establishes and what it does not

At fixed 16K context and cap 8192, the explicit thinking toggle changed two failing P0 plans into correct plans in this sample. At fixed thinking-off mode, increasing the cap had no effect on completed answers. At thinking-on mode, the larger cap was necessary for these final answers to appear. This is stronger evidence than changing all settings together, but one generation per cell and only three selected cases cannot establish a stable effect size or rule out block-order/backend variability.

The check does not isolate context capacity: it holds 16384 in every arm. Original reported inputs never exceeded 1690 tokens within a 4096 context, and every completed original input-plus-generated count was at most 2207. There was no observed original context-window exhaustion. Larger context now supplies headroom for extended generation rather than additional task evidence.

The earlier self-model loss remains a result for the tested non-thinking, capped configuration. It should not be presented as the result of testing this model at its strongest validated reasoning settings. This new P0-only check also cannot be used to claim that self-model framing works: that requires comparing P1 and P2 with identical suitable settings.

## Practical next study

Use **thinking on, context 16384 and cap 8192** as the starting configuration for development, checking completion and substantive difficulty across all six families before freezing another comparison. Increase headroom during development if necessary; do not change settings within a scored run. Choose moderate family-level difficulty using development material, then freeze new test instances without filtering their observed outcomes to force a 50% baseline failure rate.

For another framing comparison, give P0/P1/P2 the same settings and evidence. Separately cross P1/P2 with identical deterministic final-payload validation feedback and equal correction allowances if testing whether checking the actual plan helps. A validator-assisted gain must be attributed to that assisted system unless the matched P2/P1 comparison demonstrates additional framing value.

## Runtime, verification and artifacts

Total request time was **383.75 seconds**, about **6 minutes 24 seconds**; first request to last finish took 384.46 seconds. Twelve attempts generated 13651 tokens. Nine completed, three truncated, zero transport errors. The old test's inputs, outputs and scored analysis were verified unchanged. All frozen sources, exact visible messages, settings, model digest, backend and twelve unique terminal cells passed [verification](../results/2026-10-03-settings-diagnostic/verification.json). Twenty-one code tests passed, including diagnostic truncation and duplicate-cell checks.

Artifacts: [scores and every final payload](../results/2026-10-03-settings-diagnostic/settings-analysis.json), [precollection lock](../results/2026-10-03-settings-diagnostic/precollection-lock.json), and per-arm manifests, dataset snapshots and append-only event logs beneath [the diagnostic run](../results/2026-10-03-settings-diagnostic/). Reproduce scoring and verification without more model calls:

```sh
python3 scripts/run_settings_diagnostic.py --output results/2026-10-03-settings-diagnostic --analyze-only
python3 scripts/verify_settings_diagnostic.py --run results/2026-10-03-settings-diagnostic
```
