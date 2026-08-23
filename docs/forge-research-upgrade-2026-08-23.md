# NEXUS Forge — Research-Driven Upgrade Notes — 2026-08-23

Status: shadow research and architecture guidance. This note does not authorize merge, deploy, external action, permission change, or production mutation.

## Evidence basis

This pass combines retrievable NEXUS project evidence with recent public research current through 2026-08-23.

NEXUS evidence already showed recurring failure classes: stale authority, cross-project contamination, claim-to-fact promotion, duplicate architecture, connector-state drift, snapshot incompleteness, approval scope leak, hardening recurrence, no-op writes, optimistic-concurrency conflicts, retryable-vs-contained state conflation, outcome-proxy confusion, maturity inflation, duplicate outreach and uncalibrated scores.

Recent research adds four architecture implications:

1. Agent memory is a write -> manage -> read system, not just a storage layer. Memory must be task-conditioned, contradiction-aware and able to supersede stale records. Source: Du, *Memory for Autonomous LLM Agents: Mechanisms, Evaluation, and Emerging Frontiers*, arXiv:2603.07670; EvoMemBench, arXiv:2605.18421.
2. Failure trajectories are useful improvement data. Failure-driven inference-time patches improved OSWorld success from 42.3% to 48.9% in one 2026 study, without additional training. Source: Sun et al., *Learning from Failure: Inference-Time Self-Improvement for Computer-Use Agents*, arXiv:2606.31270.
3. LLM judges must not be trusted as sole promotion authorities for evidence-heavy agent work. REFLECT reports overall judge accuracies below 55% across reasoning, tool-use and report-quality failures, with particularly weak evidence verification. Source: Wang et al., arXiv:2605.19196.
4. Prompt injection in agent/MCP environments remains an execution-layer problem, not just a text-filter problem. 2026 work finds significant variation across MCP clients and emphasizes parameter visibility, sandboxing, audit logging and exact authorization boundaries. Sources: arXiv:2602.10453 and arXiv:2603.21642.

## Applied changes in PR #36

- Added `forge_failure_memory.py` with 18 evidence-linked failure patterns.
- Added task/concern-conditioned failure retrieval.
- `evaluate_registered_forge_preflight()` now retrieves internal relevant failures before checking a material change.
- Caller-supplied incident references are not automatically marked consulted; only memory actually read by the internal retrieval path is.
- Failure-memory integrity is fail-closed.
- Tests prove relevant retrieval for evaluation/security concerns and preserve the explicit caller-consultation boundary.

## Decision-system upgrade direction

The next NEXUS decision architecture should be layered rather than agent-count driven:

1. Deterministic control layer — identity, versions, approvals, dedupe, state transitions, evidence classes, exact comparisons.
2. Retrieval layer — task-conditioned current facts + prior failures + contradictions + supersession.
3. Reasoning layer — generate alternatives, hypotheses, counterarguments and missing-information plans.
4. Skeptical verification layer — source verification, adversarial tests, deterministic regressions and controlled interventions; LLM judge advisory only.
5. Decision layer — choose reversible next action by evidence, expected commercial value, downside, information gain and opportunity cost; avoid pseudo-probabilities before calibration.
6. Execution layer — smallest authorized action with idempotency, retry class, rollback/containment and audit event.
7. Outcome layer — stage-specific results, raw denominators, human correction, time/cost and final business outcome.
8. Evolution layer — propose scaffold changes from repeated patterns; compare candidate vs baseline; human-gated promotion; rollback on regression.

## New growth ideas — ranked by architecture fit

### P0 — Failure Retrieval + Contradiction Graph
Extend current failure memory into a typed graph linking Fact/Claim/Decision/Failure/Lesson/Project/Entity/Version. Retrieval should return both supporting and contradicting records and mark stale/superseded memory. This improves decision quality without adding another agent.

### P0 — Outcome-Weighted Opportunity Graph
Link Company -> Need Hypothesis -> Evidence -> Relationship Path -> Supplier Match -> Action -> Outcome. Rank next work using observed stage conversions and information gain, not raw outreach volume. Preserve ordinal decisions until enough outcomes exist for calibration.

### P0 — Shadow Autonomy Budgeter
For every autonomous cycle, enforce budgets for actions, tokens/cost, wall-clock time, external-risk class, retries and unresolved uncertainty. Safe work continues after isolated failures; budget exhaustion or risk escalation contains only the affected lane.

### P1 — Counterfactual Decision Lab
Before important decisions, generate at least one alternative hypothesis and one falsifying test. After outcome, replay: what evidence would have changed the decision? Store only lessons that survive repeated or cross-project evidence.

### P1 — Evaluation Intervention Generator
Instead of only judging outputs, programmatically mutate one variable at a time — stale source, wrong project, missing attachment, changed recipient, contradictory supplier claim, incomplete pagination — and verify the system detects the localized failure. This follows the controlled-intervention logic used by REFLECT while keeping promotion-critical checks verifiable.

### P1 — Memory Consolidator / Learned Forgetting Policy
Periodically identify duplicate, stale and superseded records. Never delete raw evidence; consolidate operational memory into one current record with lineage to predecessors. This addresses memory growth without creating a larger prompt/context dump.

### P2 — Multi-Agent Council only where decomposition earns its cost
Use specialist parallelism only for tasks with separable work and measurable benefit: e.g. technical compliance, commercial terms, sanctions/logistics, source verification. A single orchestrator retains the canonical decision and conflict-resolution contract. Do not create persistent specialist agents merely because multi-agent architecture is fashionable.

## Key anti-pattern update

NEXUS must not equate autonomy with more agents. The target is a more autonomous decision system built from better state, retrieval, verification, budgets, outcome feedback and controlled promotion. More agents are justified only after benchmarked gains exceed coordination cost and error propagation.
