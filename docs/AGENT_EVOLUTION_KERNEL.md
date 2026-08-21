# NEXUS Agent Evolution Kernel v0.1

## Purpose

Turn observed agent/tool failures into bounded experiments and evidence-backed improvement proposals without allowing recursive, uncontrolled self-modification.

## Loop

`OBSERVE -> DEDUP -> HYPOTHESIZE -> PROPOSE -> EVALUATE -> RED-TEAM -> PROMOTABLE -> HUMAN APPROVAL -> VERSIONED RELEASE`

Promotion is deliberately outside the kernel. A candidate may become **promotable**, never self-deploying.

## Research basis

The design incorporates convergent production lessons from current agent systems:

- OpenAI Agents SDK: small primitives, sessions, guardrails, human-in-the-loop, tracing/evaluation, sandboxed long-horizon work.
- Anthropic Managed Agents: separate brain/harness, hands/tools/sandboxes, and durable append-only session state so each can fail or evolve independently.
- Anthropic multi-agent research: orchestrator-worker research, durable plans/memory, deterministic safeguards, tracing, tool-testing agents, and iterative prompt/tool-description improvement.
- Anthropic long-running harness work: separate generator from skeptical evaluator; define testable contracts; use persistent artifacts rather than relying on conversational relay.
- LangGraph: combine deterministic workflow steps with agentic steps; persistence and HITL are first-class concerns.
- Temporal: distinguish saved state from durable execution; retries, durable waits, and crash recovery belong in the runtime/orchestrator.
- Microsoft Agent Framework: use workflows for well-defined processes and agents for open-ended work; do not use an agent where a deterministic function suffices.

## NEXUS design consequences

1. **No agent proliferation by default.** New permanent agents require evidence that a deterministic function or temporary specialist is insufficient.
2. **Brain / hands / state separation.** Model/harness logic must not own durable state or privileged execution environments.
3. **Independent evaluator.** The component proposing a change cannot be the only judge of that change.
4. **Evidence before confidence.** Failure observations and evaluation results require retrievable evidence references.
5. **Promotion threshold.** A candidate must beat a baseline and show no recorded safety regression.
6. **Human gate for promotion.** Changes to production prompts, tool permissions, policies, routing, deployment, or external-action authority remain consequential actions.
7. **Version everything.** Prompts, tool schemas/descriptions, policies, eval sets, routing logic, and model selections should have version identifiers and rollback paths.
8. **Learn from failures, not vibes.** Evolution proposals originate from observed failure modes, outcome gaps, cost/latency regressions, or missed opportunities.
9. **Failure observations are time-bound evidence.** Each observation carries a timezone-aware `observed_at`; deduplication keeps higher severity and uses recency to break equal-severity ties so stale failures do not silently override newer observations.

## First real replay — Hydrotester state drift, 21 Aug 2026

A real NEXUS drift event is now represented in tests rather than only in narrative documentation:

- repository manifest dated 19 Aug still treated final Hydrotester pipe length and wall-thickness/ID as unknown;
- newer retrievable Gmail/Notion evidence on 21 Aug changed the operational state;
- the failure is modeled as `canonical-state-reconciliation / repository manifest lagged newer buyer-confirmed hydrotester evidence`;
- evidence refs point to the Gmail message, canonical Notion project page, and stale GitHub manifest;
- the generated candidate proposes a freshness-aware reconciliation gate;
- because no measured baseline-vs-candidate field evaluation exists yet, the kernel keeps the candidate at `experiment`, not `promotable`.

This is the intended behavior: a real failure can create a traceable improvement candidate, but one replay or passing unit test cannot authorize production promotion.

## Next integration

Feed trace/evaluation failures, Outcome Ledger misses, CI regressions, stale-state drift, connector failures and research-quality defects into `FailureObservation`; run candidate changes in isolated evaluation; record results; surface only promotable candidates to the approval layer.
