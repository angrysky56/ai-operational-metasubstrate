# Project evaluation policy

Ty's October 3, 2026 instructions govern new evaluation work:

- All new local `ornith-aq1.5:35b` evaluations use thinking enabled, context
  16384 and generation cap 8192. Use `scripts/run_locked_ollama.py` and the
  recorded settings profile. Do not use the legacy collector's non-thinking
  defaults for a new run or weaken reasoning to manufacture baseline failures.
- Apply the same pre-output rule, settings, records, review budgets and
  correction opportunities across compared conditions. Require observed
  thinking-before-answer order and revalidate the actual final object before
  acceptance. A reasoning trace is not proof of faithful computation.
- Freeze protocol, source, dataset and settings before collection; keep exact
  request/response logs and all failed attempts. Do not silently change a frozen
  study, repeat terminal answers or resubmit an uncertain request.
- Preserve historical datasets, collectors, protocols and result artifacts.
  Their frozen settings describe historical evidence; current settings belong
  to a new experiment version. Do not rewrite old scores to favor a hypothesis.
- Runtime checks receive visible evidence and policy, never benchmark keys.
  Code owns exact source filtering, arithmetic, constraints and permissions;
  Jev makes narrow semantic judgments. Recover full persisted review batches;
  the immediate result is only a preview. A semantic score never overrides a
  deterministic failure, unsupported policy or missing required review.
- Label reused author-designed tasks as exploratory. Separate final payload
  correctness, semantic consistency, accepted drafts and incomplete outputs.
  Report ceilings and adverse results forthrightly. Shared checker predicates
  do not constitute independent validation.
- Keep the project self-contained. External MCP services are configured
  dependencies; never import code from a sibling checkout or hardcode its path.
- Operational audits concern the assistant's actual project work, using source
  artifacts and explicit behavioral criteria. Do not impose a personal routine
  or collect Ty's private-life data. Missing evidence stays missing, and an
  empirical quantity alone does not prove a virtue.
