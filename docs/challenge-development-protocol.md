# Challenge development protocol

October 3, 2026 · Development only · Author-designed synthetic cases

The previous pilot hit a 24/24 baseline ceiling. This phase tests the difficulty and integrity of new cases before a fresh held-out evaluation. It is not evidence confirming OM-KT efficacy.

An approximately 50% baseline case failure rate is a useful development target, not a scientific requirement or a score to force. Use a provisional acceptable band of **4–8 failed complete cases out of 12** (33–67%), preferably spanning at least two families. Twelve cases cannot precisely estimate a population failure rate. A complete case now contains several decisions; report atomic check counts as well, so a high all-or-nothing failure rate does not hide mostly correct work.

Build twelve cases, two per family: premise, access, action, means, stakes, revision. Require complete structured status maps or plans. Evidence is longer, unordered, and includes stale records, similar identifiers, proposed drafts and confident claims. Authority and permission rules remain explicit. Embedded record text is data, not a user/system instruction. Do not degrade model settings, invent ambiguity, or mark valid alternatives wrong to obtain failures. Each schedule accepts every feasible ordering, not just a preferred reference.

Use identical P0/P1 system text and the same installed `ornith-aq1.5:35b` digest as pilot v1. Retain all inference settings: temperature 0, seed 42, context 4096, output cap 1024, top_k 20, top_p 0.95, thinking disabled. No grammar-constrained decoding is added; requesting JSON is part of the identical user task. The same existing runner uses `/api/chat`; its routing and output-status rules are unchanged. [Ollama Chat API](https://docs.ollama.com/api/chat)

Collect twelve cases × P0/P1 = **24 attempts per development version**, with order seed 20261006, a 7200-second run limit and 600-second per-request timeout. No wrong-answer retries. Retain missing, invalid, and truncated cells. A maximum of three separately identified development versions (72 attempts total) may be explored in this phase. Each revision must be frozen before its own generation; document changes and preserve earlier outputs. Changes are development adaptation, never held-out validation.

Primary development score is complete correctness of the requested structured payload, using deterministic frozen checks. Accept one JSON object with optional surrounding prose/fences; list order is ignored where only membership matters. Reject duplicate set members, missing decisions, wrong types, incomplete schedules, violated prerequisites, and unauthorized commit flags. Optional rationale is not machine-scored, and unsupported prose outside the payload requires a separate audit. No automatic LLM judge is used. Report substantive payload errors separately from unparseable responses and backend failures. A parse-error-driven apparent 50% does not qualify the bank as meaningfully difficult.

Audit keys before generation by resolving the supplied source records with separately written code. Enumerate schedule solutions to prove feasibility. This is an internal code cross-check, not independent ground truth or independent human review. The author remains the sole conceptual reviewer. Freeze the bank, builder, checker, audit code, runner and this protocol before generation.

If the difficulty band and multi-family substantive-error check are reached, stop adapting the development set. Next freeze a separate 24-case test bank under P0/P1/P2 with prospective analysis and unchanged model settings. Its realized baseline rate is reported as observed; **do not discard or replace test cases to achieve 50%**. Independently review new keys and ratings when another reviewer is available. Closely related generated variants test transfer within templates, not independent-domain generalization.

If development remains at ceiling, revise with an explicit reason and a new version; do not spend on a second model or call the previous tie efficacy evidence. If three versions remain unsuitable, stop with the development failure documented and a concrete next-design proposal. Generic mathematical difficulty alone does not establish relevance to operational self-modeling.

This approach separates item development from measuring a treatment effect. Work on adaptive AI evaluation motivates attention to item difficulty and validity; it does not establish that exactly 50% failure is optimal for this intervention. [Zhuang et al., ICML 2025 position paper](https://arxiv.org/abs/2306.10512)
