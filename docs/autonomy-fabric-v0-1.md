# NEXUS Autonomy Fabric v0.1

## Purpose

Create one deterministic planning layer for the user's desired always-improving business/engineering system without creating an uncontrolled agent swarm or a second authorization framework.

The fabric converts candidate work into three explicit queues:

1. `runnable` — safe/reversible work with a verified capability;
2. `human_gate` — consequential work or connector/plugin changes requiring exact human approval;
3. `blocked` — unresolved, malformed or unsupported work.

It does **not** execute tools itself. Existing connector runtimes remain the execution surface.

## Loops this fabric coordinates

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

Evidence order is explicit: `strong -> partial -> weak -> unverified`.

Malformed priority/evidence/cost fields are ranked last so they can reach validation and fail closed. Invalid WorkItems do not reach capability selection or an action gate built from malformed values.

These tiers are reviewable and can later be calibrated against real outcomes using PR #7 Decision Learning.

## Cross-AI evidence boundary

- AI review without underlying code/data access is `unverified`.
- Code-read review is at most `partial` until claim-level verification against the current code/data/tests.
- Review evidence is research input, not authorization.
- A research/review WorkItem cannot silently acquire write/send/access capability; consequential escalation must become a new explicit human-gated WorkItem.

## Security boundaries

- External send, merge, production deploy, access changes, public publication/visibility changes, destructive actions, contracts/POs, payments and signatures remain human-gated by the canonical PR #4 policy.
- Plugin or connector installation/permission changes are `change_access` actions and are not self-authorized.
- Missing capabilities remain blocked; the fabric must not invent integrations.
- Work metadata is bounded and rejects Unicode control/formatting characters to avoid ambiguous control-plane IDs.
- Evidence refs are required so autonomous planning cannot manufacture unsupported tasks.
- This is not a self-modifying model. Proposed upgrades are ordinary work items that must pass the same gates, tests and review process as other code.

## Backup and reconstruction contract

A backup is not considered proven merely because a destination file exists.

`SnapshotEntry` binds an artifact to:
- `source_ref`;
- exact `source_version_ref`;
- content SHA-256.

`BackupReceipt` proves that the exact source version/digest was written to a backend. Matching digest alone does not prove freshness.

`RestoreProof` then binds a read-back/reconstruction attempt to the same checkpoint, artifact, backend, stored artifact, exact source version and expected digest. Reconstruction proof succeeds only when the restored content digest exactly matches the expected stored digest.

This proves byte/content reconstruction for that artifact only. It does **not** prove application-level semantic recovery, production readiness or permission to overwrite canonical state.

## Current technical research alignment

The design intentionally stays small. OpenAI Agents SDK provides a compact set of agent/tool/handoff/guardrail primitives plus sessions, human-in-the-loop and tracing; NEXUS should adopt a model-managed worker only after the deterministic fabric demonstrates a measured need. MCP's host/client/server architecture remains relevant for future connector portability and capability isolation. Any future model/tool tracing must preserve NEXUS data minimization and must not turn sensitive commercial payloads into an observability exfiltration surface.

## Planned increments

### v0.1 — current
Deterministic planning, source adapters, capability routing, human-gate classification, blocked-state preservation, Cross-AI evidence tiers, backup manifests/receipts, exact source-version freshness and reconstruction proof, plus adversarial metadata tests.

### v0.2 — measured pilot
Run real safe source cycles from Gmail/GitHub/Notion/research and record useful-vs-noise outcomes. Add no new scheduler until the pilot produces enough outcomes to justify calibration.

### v0.3 — after measured need
A worker runner for selected safe task classes with idempotency keys, retry budgets and checkpointing. No autonomous consequential actions.

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
