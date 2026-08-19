# NEXUS Eval Harness v0.1

## Purpose

Provide a small, deterministic evaluation contract for NEXUS changes before promotion. The harness is intentionally code-first and provider-portable: it records cases, measured results, critical failures and explicit promotion policy without depending on a hosted eval product.

## Research basis

Current evaluation guidance supports several design choices used here:

- Real-world cases and costly edge cases should be part of the dataset, not only synthetic happy paths.
- Evaluation configuration/harness details matter; the tested system version and config must be recorded alongside results.
- Deterministic/programmatic graders are preferred when a property can be checked exactly; human/domain review remains important for ambiguous quality judgments.
- Headline pass rates must not hide critical failures, policy violations or unsupported claims.
- Current OpenAI guidance recommends code-based Agents SDK workflows for workflows that need to persist beyond the hosted Agent Builder/Evals product lifecycle, so this harness avoids a hard dependency on hosted Evals.
- NIST AI RMF / GAI profile emphasizes lifecycle testing, evaluation, verification and validation rather than one-time launch scoring.

Primary references reviewed 2026-08-19:

- OpenAI, “A shared playbook for trustworthy third party evaluations” (2026-05-29)
- OpenAI, “How evals drive the next chapter in AI for businesses” (2025-11-19)
- OpenAI, “Introducing AgentKit” with 2026-06-03 lifecycle update
- NIST AI RMF / NIST AI 600-1 Generative AI Profile

## v0.1 data model

`EvalCase` describes the objective, input reference, domain and whether the case is critical.

`EvalCaseResult` records only observed/measured counts and evidence references:

- pass/fail
- unsupported claims
- policy violations
- human overrides
- failure tags
- evidence references

`EvalRun` records the exact system version, harness version and configuration reference.

`PromotionPolicy` is explicit policy, not hidden model judgment. Promotion can be blocked by:

- pass rate below the configured threshold;
- unsupported-claim budget exceeded;
- policy-violation budget exceeded;
- any critical case failure when zero critical failures are required.

## First golden cases

1. **Evidence semantics — critical:** supplier claims must not silently become verified facts.
2. **Human gate — critical:** consequential external actions remain human-approved.
3. **Requirement readiness:** decision-critical engineering unknowns stay explicit rather than becoming authoritative values.

These cases map directly to current NEXUS failure modes and draft PRs; they are not generic benchmark trivia.

## What this harness does not do

- It does not call an LLM grader.
- It does not invent a single “NEXUS intelligence score.”
- It does not treat pass rate as sufficient when a critical safety/business rule fails.
- It does not automatically merge, deploy or send anything.
- It does not replace business outcome evaluation.

## Next step

After CI is green, run shadow evals against concrete artifacts from PR #1, PR #2, PR #4 and future Decision Learning outputs. Add new golden cases only when a real failure mode or costly edge case is observed. If later an LLM grader is introduced, its judgments must be audited against human/domain review before it can influence promotion.
