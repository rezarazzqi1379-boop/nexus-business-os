# PLO Consolidation Review v0.1

Status: REVIEW CONTRACT ONLY — no runtime promotion, deploy, production write or external action authority.

## Why this exists

PR #40 contains a substantial durable-execution implementation (Linux/Docker/PostgreSQL, leases, fencing, idempotency, orphan recovery and reconciliation) but it was developed from an older base and now overlaps with a newer main branch that contains NEXUS Brain v0.4. Directly merging the 50+ commit branch would risk restoring stale architecture, duplicating control authority or obscuring the newer Brain/live-command boundaries.

The consolidation goal is therefore **selective transplant, not branch merge**.

## Current authoritative ownership

- NEXUS Brain: governed evidence, project relationships, canonical/live decision projection and internal next-action recommendations.
- Project Masters / Source Registry: Tier A authority and source precedence.
- Exact external-action approval: must remain a separate canonical action gate; PLO may consume approval but must never mint or reinterpret it.
- PLO candidate: durable execution state only.

## PLO capabilities worth preserving

The following capabilities are strategically useful and should be extracted behind a small interface if their current implementations survive adversarial review:

1. durable task/run state;
2. queue claiming with leases;
3. fencing or task-version checks against stale workers;
4. immutable idempotency binding to action/control snapshots;
5. orphan recovery after lease expiry or worker crash;
6. provider reconciliation after ambiguous external state;
7. read-only completion path separated from consequential execution;
8. PostgreSQL concurrency/durability implementation;
9. Linux/Docker worker packaging;
10. duplicate-execution telemetry.

## Capabilities that must NOT become PLO authority

PLO must not own or invent:

- engineering/commercial truth;
- project requirements;
- supplier qualification;
- opportunity scoring authority;
- approval issuance;
- message content approval;
- connector permissions;
- source promotion;
- Brain contradiction resolution;
- autonomous send policy.

A textual approval reference is provenance only unless the canonical action gate verifies the exact immutable action snapshot.

## Consolidated target boundary

`Brain / Control -> immutable ExecutionIntent -> canonical approval check if consequential -> Durable Executor -> provider -> reconciliation/outcome -> Brain/Outcome Ledger`

The Durable Executor accepts no free-form business reasoning. It consumes a fully scoped immutable intent with project identity, action class, payload digest, source/control refs and idempotency key.

## Required ExecutionIntent fields

- execution_intent_id
- project_id
- action_class (`read_only`, `reversible_internal`, `consequential_external`)
- operation_type
- normalized payload or payload digest
- canonical/control snapshot refs
- live-evidence refs where relevant
- idempotency_key bound to immutable fingerprint
- created_at
- expiry/review condition where relevant
- approval binding for consequential external actions

## Mandatory fail-closed invariants

1. Changed payload + reused idempotency key -> reject.
2. Changed project + reused idempotency key -> reject.
3. Changed canonical/control snapshot + reused idempotency key -> reject.
4. Stale lease cannot complete or commit an operation.
5. Unknown provider state after a potentially-effectful call -> reconciliation, not blind retry.
6. Read-only completion cannot be used for consequential operations.
7. Brain blockers cannot be bypassed by durable execution state.
8. PLO cannot promote Tier B evidence to Tier A.
9. Exact approval must match the final immutable consequential action snapshot.
10. No runtime component may claim production maturity solely from CI/shadow success.

## Migration strategy

Do not rebase/merge PR #40 wholesale into current main. Instead:

1. freeze PR #40 as an implementation evidence branch;
2. inventory reusable runtime modules (`plo_core`, PostgreSQL store/isolation, reconciliation, worker/Docker packaging);
3. extract the smallest executor interface on a fresh branch from current main;
4. add a Brain-v0.4 -> read-only ExecutionIntent replay first;
5. run crash-window, stale-lease, duplicate-key and changed-envelope adversarial tests;
6. only after those pass, connect canonical exact-action approval for consequential paths;
7. keep all provider writes disabled until a separate production-readiness gate.

## First integration target

Use the current Hydrotester command projection. It already exposes blocking unknowns and live GH evidence. The first executor integration should perform **read-only/internal normalization work only**, such as creating a durable research/normalization task bound to the GH live-evidence node and current project-control snapshot. No email send and no supplier-selection action is authorized.

## Promotion criteria

The consolidated executor may move from candidate to merged shadow component only when:

- current-main regression suite stays green;
- exact branch-head dedicated runtime tests are green;
- duplicate execution remains zero under concurrency/adversarial replay;
- stale workers cannot commit;
- ambiguous provider state reconciles without blind resend;
- canonical Brain/project blockers remain unchanged by runtime state;
- no competing approval or source-authority layer is introduced;
- rollback path is documented and exercised.

Deployment and production authorization remain separate later gates.
