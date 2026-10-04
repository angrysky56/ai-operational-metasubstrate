# AI Operational Metasubstrate

Can a language model make fewer mistakes by using a fallible model of its own failure tendencies, without inventing a personality or pretending to inspect its internal computation?

**Status: working local runner and bounded feedback harness, with completed framing, settings and mechanism checks. OM-KT efficacy has not been established.**

New Ornith evaluations now use a locked collector: **thinking on, context
16384, generation cap 8192**, pinned model digest and identical pre-output checks.
The [balanced 24-case P1/P2 protocol](docs/balanced-feedback-v2-protocol.md) covers
48 initial answers plus 48 equally assisted corrections. The collector records
actual thinking-before-answer order. These settings reduce the observed budget
problem; truncations remain possible and never receive completion credit.

The [completed balanced matrix](docs/balanced-feedback-v2-report.md) ran all
**96 actor calls**: P1 ordinary guidance and P2 self-model framing each finished
with **24/24 correct, accepted plans**. P1 already scored 24/24 initially; P2
scored 23/24 because one answer exhausted the 8K generation cap without final
JSON. Its planned correction recovered that output. No correct plan regressed.
All 190 requested Jev judgments were recovered and the saved-record audit passed
460 checks. Reviewer cost was an estimated **$0.00551072** at Ty's supplied rate;
billing was unreported. Local actor request time was about 96½ minutes.

This is correct-plan preservation at a ceiling, with **no demonstrated extra
self-model benefit** and no substantive initial errors to repair. Fresh cases
need headroom under the intended P1 settings. Approximately 50% failure is a
development guide, not a quota achieved by weakening reasoning or selecting test
failures. The matrix has no self-check-only arm, so it cannot isolate the
contribution of external checking or Jev alone.

| Preserved study | Result and scope |
| --- | --- |
| [First 72-response pilot](docs/pilot-v1-report.md) | P0/P1/P2 each 24/24; an uninformative ceiling |
| [Harder 72-response test](docs/challenge-test-v1-report.md) | P0 9/24, P1 10/24, P2 6/24; adverse local result with thinking off and cap 1024 |
| [Controlled settings diagnostic](docs/settings-diagnostic-report.md) | Thinking off 0/3 at either cap; thinking on 0/3 at 1024, 2/3 at 8192, fixed 16K context |
| [Six-case matched feedback](docs/feedback-development-report.md) | P1 initially 6/6; SELF, CODE and JEV preserved 6/6; reviewer preview omission preserved and fixed |
| [Jev semantic boundary check](docs/jev-semantic-stress-report.md) | 12/12 authored labels matched, including two embedded commands; consistent wrong-source plan still rejected by code |
| [Balanced 24-case P1/P2 matrix](docs/balanced-feedback-v2-report.md) | Final 24/24 each; one incomplete-output recovery, no substantive repair estimate or framing gain |

These studies have different endpoints and settings; their scores are not pooled.
The old payload errors included source selection, logical gates, schedule
constraints and corrections absent from the actual object, beyond truncation.
See the [failure analysis](docs/failure-analysis.md). The new thinking profile and
shared pre-output rule cannot be credited separately from this matrix.

Operational Metasubstrate for Know-Thyself (OM-KT) proposes a practical sequence: examine the evidence, identify permissible actions, then optimize within those boundaries. Its distinctive rule, **Clear Sight in Crisis**, says that invoking a serious safety constraint must preserve scrutiny of whether the constraint actually applies. Uncertainty should support proportionate protection and further checking, while accounting for the harm that delay can cause.

The important experiment is whether the operational self-model adds anything beyond equally good ordinary reasoning instructions. Better-sounding answers alone would not establish that it does.

## Start here

- [Latest balanced results](docs/balanced-feedback-v2-report.md) and [frozen protocol](docs/balanced-feedback-v2-protocol.md): all 96 actor calls and 190 semantic reviews, with the complete saved-record audit.
- [Project evidence audit](docs/operational-evidence-audit.md): claims checked against experiment logs, with no personal routine or records required.
- [Research plan](docs/research-plan.md): a bounded Ollama pilot, optional Colab replication, scoring rules, and requirements for stronger claims.
- [Prompt protocol](docs/prompt-protocol.md): the three initial conditions and six public development examples.
- [Formal source review](docs/formal-source-review.md): what the Paraclete formulas support, corrections to their dependency explanations, and a reproducible check.
- [Local development results](docs/local-smoke-report.md): all 18 requests completed on an installed 35B model, with recorded timings and observed answer defects.
- [Pilot v1 protocol](docs/pilot-v1-protocol.md): 24 new cases, frozen scoring rules, and a 72-attempt limit. The bank is author-designed; independent review remains needed.
- [Pilot v1 results](docs/pilot-v1-report.md): all 72 responses completed locally in about 5½ minutes; all conditions tied. Raw answers, ratings, and analysis are preserved.
- [Challenge development protocol](docs/challenge-development-protocol.md): new structured plans and deterministic checks, aiming for moderate baseline difficulty before a separate held-out test.
- [Challenge development results](docs/challenge-development-report.md): baseline had 5/12 substantive failures; ordinary guidance did not improve complete-plan performance.
- [Challenge instance-test protocol](docs/challenge-test-v1-protocol.md): 24 new factual instances in six shared templates, with final-payload scoring fixed before collection.
- [Challenge instance-test results](docs/challenge-test-v1-report.md): the adverse comparison, safety-flag coverage, raw outputs, and revised mechanism-study plan.
- [Failure analysis](docs/failure-analysis.md): completed errors beyond truncation, including stale records, incorrect rule application and corrections that never reached the final plan.
- [Settings diagnostic protocol](docs/settings-diagnostic-protocol.md): a bounded check of thinking mode and generation budget with 16K context, separate from the original comparison.
- [Settings diagnostic results](docs/settings-diagnostic-report.md): thinking with an 8K generation budget repaired two of three selected development plans; one evidence-source error persisted.
- [Jev harness design](docs/jev-harness-plan.md): the implemented generator/checker split, original reviewer probe and next evaluation design.
- [Matched feedback protocol](docs/feedback-development-protocol.md) and [results](docs/feedback-development-report.md): shared initial answers, three correction arms, the documented retrieval defect and separately verified recovery.
- [Jev semantic boundary protocol](docs/jev-semantic-stress-protocol.md) and [results](docs/jev-semantic-stress-report.md): explicit corrections, unresolved conclusions, embedded commands and consistency versus source truth.
- [Original white paper](docs/know_thyself_operational_metasubstrate_white_paper.docx): the October 2026 conceptual proposal. The research plan refines its evaluation design; the original is preserved.

These materials are for researchers and contributors who want to evaluate the idea. A small local runner, six development cases, and a separate 24-case exploratory bank are included. Independent case review and independent rating remain needed. There is no installable agent or Colab notebook in this project.

## A practical route with existing resources

Start with an already installed local instruction-following model through Ollama. Six development examples across three conditions require 18 responses to check the procedure. A separate 24-case exploratory pilot requires 72 responses. No paid API is required for either stage, although local inference consumes time and electricity.

Colab Pro can support a later open-weight replication if its assigned hardware and available compute units permit it. It does not guarantee a particular GPU or access to a hosted frontier model. The plan begins with existing resources and fixed stopping limits rather than assuming new purchases.

Small models are useful for testing the runner and rubric. Their results cannot settle how the method behaves on more capable models. Model size by itself is also not a sufficient measure of suitability.

## Contributions that would help

- Independently review the case bank and contribute a new, more discriminating held-out bank.
- Review cases and score blinded answers; include benign situations and harms caused by unnecessary delay.
- Contribute a documented run on an independent model family, including null or negative results.
- Supply feedback on the operational rules or the formal source review.

Use the same tasks, constraints, and inference settings for every condition. Preserve raw results and identify the exact model and prompt versions. Do not use the model's agreement with its own self-description as evidence that the description is true.

## Run the development check

Requires Linux, Python 3.10 or newer, the system's existing `curl`, and a running
Ollama service with the pinned local Ornith model. No Python packages are required.
Cloud aliases are rejected. A different model requires its own documented profile.

For new Ornith runs, use `scripts/run_locked_ollama.py`. It records streaming
output order and uses an absolute transfer deadline. `run_ollama.py` remains the
historical collector for preserved provenance; its old defaults must not govern
new evaluations.

First inspect the plan without generating responses:

```sh
python3 scripts/run_locked_ollama.py --model ornith-aq1.5:35b --output results/my-smoke --dry-run
```

Then run up to three new responses at a time:

```sh
python3 scripts/run_locked_ollama.py --model ornith-aq1.5:35b --output results/my-smoke --limit-new 3
```

Repeat the same command to resume. Defaults cap the entire run at 18 attempts and two hours of accumulated request/session work, with a ten-minute request timeout. A wrong answer is saved without retry. An error or truncation stops the invocation for review; previous terminal attempts remain counted on resume. A checkpoint with an uncertain unfinished request blocks resubmission. Keep settings and frozen inputs unchanged for a resumed run.

Outputs include a manifest, frozen dataset, append-only request/response log, and a rating packet with a separate treatment mapping. The script does not automatically score answers or establish a research conclusion. Use a reviewer who has not opened the mapping when blinded scoring is required.

The default dataset is development material only. To change the published development fixtures, edit the prompt protocol and run `python3 scripts/freeze_development.py`; use a new result directory for changed material. The separate pilot bank is in `data/pilot-v1.json`. Its case builder is `scripts/build_pilot.py`; changing it creates a new study version, not a replacement for collected results.

## Run the exploratory pilot

Read the pilot protocol and freeze a new version before collecting a run. The
locked collector changes the historical settings and adds a shared pre-output
rule, so new results must not be labeled a reproduction of the original pilot.
To collect the same number of cells under current settings:

```sh
python3 scripts/run_locked_ollama.py --model ornith-aq1.5:35b --dataset data/pilot-v1.json --output results/my-pilot --max-attempts 72 --limit-new 72 --order-seed 20261004
```

Score every answer in `rating-packet.json` without opening `rating-map.json` or the raw generation log. Save ratings before joining conditions. The protocol defines the required binary fields, exact overhead quotations, and rationale. Then analyze the saved ratings:

```sh
python3 scripts/analyze_pilot.py --run results/my-pilot --ratings results/my-pilot/ratings.json
python3 scripts/summarize_run.py --run results/my-pilot --ratings results/my-pilot/ratings.json
```

The analysis retains missing cells in the planned denominator and reports the paired comparison, family counts, failure flags, and the frozen continuation rule. The summary exports runtime, answer length, and case scores. Both read the treatment mapping and should run only after masked ratings are saved. These constructed cases and a single reviewer cannot establish general reliability. The completed v1 bank is now development material for future studies; a new held-out bank is required for a fresh claim.

## Check the harder structured plans

The challenge bank requires complete status maps or constrained plans. Its deterministic checker evaluates the requested payload, not the optional prose. These are separate endpoints from the first pilot's single-reviewer answer scores; do not pool them.

To recompute saved development scores without model calls:

```sh
python3 scripts/grade_challenge.py --run results/2026-10-03-challenge-dev-v1
```

To score a completed new-instance test:

```sh
python3 scripts/analyze_challenge_test.py --run results/2026-10-03-challenge-test-v1
```

The test accepts the last complete JSON object so a corrected final plan can succeed. Development used a stricter one-object rule; its results remain preserved. Both stages retain failed attempts. The test is an instance holdout within shared templates, with no independent human case review.

To check the runner's boundaries without calling a model:

```sh
python3 -m unittest discover -s tests -v
```

## What has been checked

The feedback harness supports six explicit fictional policies. Code filters visible source records, resolves revisions, validates the actual plan and binds reviews to exact candidate/source text. Jev supplies at most two narrow semantic judgments per candidate. There is one correction opportunity and a final gate; no real-world execution. Unsupported policies, ambiguous evidence, changed candidates and missing required reviews fail closed. The workflow has been live-tested for correct-plan preservation on all 24 reused cases and one incomplete-output recovery; repair efficacy on fresh substantively failing tasks remains untested.

Forty-one code tests pass, including full MCP result retrieval beyond the five-item preview, row-order-independent conflict detection, stale reviews, uncertain-request refusal, locked settings and observable pre-output ordering. All 36 published challenge cases have matching visible-record and keyed checks. Those checks share low-level predicates and the same author; independent review remains needed.

The narrow transcribed formal core has been checked exhaustively over 256 Boolean assignments. The displayed Clear Sight implications hold, but some source explanations overstate axiom dependencies and what formal entailment establishes about real behavior. This is not a reproduction of the historical Prover9/Mace4 runs or a verification of the entire framework.

To repeat that dependency-free check from the project directory:

```sh
python3 scripts/check_formal_core.py
```

The project does not claim consciousness, privileged introspection, an empirically established universal moral theory, or a prompt-enforced security boundary.

## Run a new matched feedback check

The Python orchestration needs no packages. The MCP adapter requires Node.js
24.12 or newer, the Codex CLI with a configured `jev` stdio server, and that
server's existing provider credentials and pinned `omkt_payload_consistency` v1
capability. The client has its own dependency lockfile and imports no sibling
project.

For a fresh compatible Jev server, load the project-owned
[capability definition](results/2026-10-03-jev-probe/payload-capability.json)
using that server's capability-definition tool. Verify version 1 and hash
`3d4ee30843872289b08aee9c74e22cb65db405631b0fa6b06cc1ebe799623544` before
collection. The runtime checks this identity and does not create or replace
capabilities during an evaluation.

Install the small SDK dependency:

```sh
npm ci --prefix harness
```

Use a new directory and read the
[balanced matrix protocol](docs/balanced-feedback-v2-protocol.md). It covers all
24 published challenge instances under P1/P2, with equal checking and one
correction each: at most 96 local actor calls and 192 semantic judgments, with a
four-hour accumulated actor request-time ceiling. These reused instances are
exploratory material.

```sh
python3 scripts/run_balanced_feedback.py --output results/my-balanced-feedback --stage all
python3 scripts/verify_balanced_feedback.py --run results/my-balanced-feedback
```

Preparation freezes the mechanism before reading new initial answers. Correction
inputs are then frozen before generation. A known terminal length stop may
resume untouched cells with the same collection command; an uncertain request
must be reviewed. No terminal answer or started MCP judgment is automatically
resubmitted. The earlier six-case collector remains a preserved mechanism
study; new evaluations use the locked matrix collector. A new held-out bank
and matched control workflows are needed to estimate repair efficacy or Jev's
incremental contribution.

Recheck the preserved experiments without any new model calls:

```sh
python3 scripts/verify_balanced_feedback.py --run results/2026-10-03-balanced-feedback-v2
python3 scripts/verify_feedback_development.py --run results/2026-10-03-feedback-development
python3 scripts/run_jev_semantic_stress.py --output results/2026-10-03-jev-semantic-stress-v1 --verify-only
```
