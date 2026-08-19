# NEXUS Autonomy Fabric v0.1

## Purpose

Create one deterministic planning layer for the user's desired always-improving business/engineering system without creating an uncontrolled agent swarm or a second authorization framework.

The fabric converts candidate work into three explicit queues:

1. `runnable` — safe/reversible work with a verified capability;
2. `human_gate` — consequential work or connector/plugin changes requiring exact human approval;
3. `blocked` — unresolved, malformed or unsupported work.

It does **not** execute tools itself. Existing connector runtimes remain the execution surface.

## Loops this fabric is intended to coordinate

- research and literature monitoring;
- market intelligence and news monitoring;
- customer-network expansion and prospect research;
- inbox monitoring and reply classification;
- coding/security learning and repository hardening;
- internal backup/knowledge organization;
- innovation and infrastructure proposals;
- capability/plugin discovery;
- security review and connector-health checks.

Each loop must produce evidence-backed candidate work rather than silently mutating the system.

## Architecture

`Signal / request -> WorkItem -> validation -> ordinal priority -> CapabilityNeed -> Capability Runtime -> ActionIntent -> Human Gate -> runnable / human_gate / blocked`

The branch is stacked on PR #4 because PR #4 already owns capability routing and action-specific human approval. This feature deliberately reuses those primitives rather than creating another connector registry or authorization model.

## Priority semantics

v0.1 does not assign fake business-value percentages. It ranks by explicit ordinal tiers:

`value -> urgency -> evidence strength -> cost -> stable task_id`

These tiers are reviewable and can later be calibrated against real outcomes using PR #7 Decision Learning.

## Security boundaries

- External send, merge, production deploy, access changes, destructive actions, contracts/POs, payments and signatures remain human-gated by the canonical PR #4 policy.
- Plugin or connector installation/permission changes are `change_access` actions and are not self-authorized.
- Missing capabilities remain blocked; the fabric must not invent integrations.
- Work metadata is bounded and rejects Unicode control/formatting characters to avoid ambiguous control-plane IDs.
- Evidence refs are required so autonomous planning cannot manufacture unsupported tasks.
- This is not a self-modifying model. Proposed upgrades are ordinary work items that must pass the same gates, tests and review process as other code.

## Current technical research alignment

The design intentionally stays small. OpenAI Agents SDK currently recommends a small set of primitives (agents, tools/handoffs, guardrails) and provides sessions, human-in-the-loop and tracing; NEXUS should adopt that runtime only when the deterministic fabric has a measured need for model-managed multi-step execution. MCP's host/client/server architecture is relevant for future connector portability and capability isolation. OpenAI tracing can capture sensitive model/tool inputs by default, so a future Agents SDK adapter must explicitly disable sensitive trace payload capture for NEXUS commercial workflows and preserve PR #10's metadata-only canonical audit state.

## Planned increments

### v0.1 — current
Deterministic planning, capability routing, human-gate classification, blocked-state preservation, adversarial metadata tests.

### v0.2 — after integration proof
Adapters that translate current Automations/Gmail/GitHub/Notion research outputs into `WorkItem` objects. Read-only or reversible internal work only.

### v0.3 — after measured need
A worker runner for selected safe task classes with idempotency keys, retry budgets, checkpointing and backup manifests. No autonomous consequential actions.

### v0.4 — only if justified
Optional Agents SDK worker for research/synthesis tasks. Tool guardrails, limited concurrency, explicit budgets, sensitive tracing disabled and deterministic eval replay required before promotion.

### v0.5 — only after real outcome data
Outcome-based scheduler calibration using Decision Learning. Kill or downgrade loops that do not improve measurable business or engineering outcomes.

## Non-goals

- no unlimited self-replication;
- no automatic plugin installation;
- no automatic permission broadening;
- no autonomous mass outreach;
- no autonomous merge/deploy/payment/contract actions;
- no second CRM, eval engine, audit schema or capability registry;
- no claim that more agents means more capability.
