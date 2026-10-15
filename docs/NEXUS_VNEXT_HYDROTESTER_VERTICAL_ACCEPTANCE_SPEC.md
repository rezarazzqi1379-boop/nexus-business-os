# NEXUS vNext — Hydrotester Vertical Acceptance Specification

Status: DESIGNED
Target project: PRJ-HYD-01
Branch scope: review-only; no production deployment or external action authorized.

## Objective

Prove one governed end-to-end path using existing NEXUS primitives before adding new architecture:

`Inbound Evidence -> Source -> Entity Resolution -> Project Isolation -> Claim -> Requirement -> Contradiction/Supersession -> Decision -> Approval -> Action -> Outcome -> Lesson`

The vertical is PASS only when provenance, project isolation, identity resolution, supersession, approval binding, replay protection, and outcome recording are all demonstrated together.

## Existing primitives to reuse

- `AuditLog`: append-only tamper-evident hash chain.
- `ApprovalStore`: exact-scope, TTL-limited, single-use approvals bound by action digest.
- `BusinessOSVault`: atomic request publication, request digest, project validation, no external writes by default.
- Supabase entities/identity candidates/aliases.
- Supabase sources/evidence/claims/claim-evidence.
- Supabase projects/project-links/requirements/proposals/proposal-claims.
- Supabase interactions/outcomes/lessons/experiments/promotion-gates.
- Supabase action-risk taxonomy and agent restrictions.

No new independent Counterparty, Relationship Capital, Company Digital Twin, or Opportunity database is permitted for this vertical. Those concepts must be projections/read-models over canonical entities, interactions, relationships, events, and outcomes.

## Required event envelope

Every state-changing event in this vertical MUST carry:

- `event_id`
- `event_type`
- `occurred_at`
- `actor`
- `project_key`
- `entity_id` or explicit `identity_state=unresolved`
- `source_ref` where evidence-derived
- `causation_id` where derived from a prior event
- `correlation_id` for the end-to-end case
- `payload_digest`
- `schema_version`
- `supersedes_event_id` when applicable

An unresolved identity MUST block supplier-specific consequential action.

## Hydrotester fixture

Use a synthetic Hydrotester case modeled on PRJ-HYD-01 without copying live supplier data into tests.

Canonical fixture requirements:

- project: `PRJ-HYD-01`
- OD range requirement
- pressure capability requirement
- hold-time requirement
- throughput requirement
- tooling scope requirement

Synthetic supplier identities MUST include intentionally confusable aliases to exercise entity resolution.

## Acceptance gates

### G1 — Project isolation

Given evidence assigned to `PRJ-HYD-01`, no claim, requirement comparison, action, outcome, or lesson may attach to KCl/SOP, Can Forming, Heat Treatment, or another project.

PASS criteria:
- cross-project write attempts are rejected;
- project key remains present across the entire correlation chain;
- a regression test demonstrates contamination failure.

### G2 — Entity resolution

An incoming sender/domain/alias must resolve to one canonical entity or remain unresolved.

PASS criteria:
- exact canonical identity resolves deterministically;
- ambiguous aliases generate an identity candidate and block supplier-specific action;
- manual resolution can be recorded with provenance;
- no irreversible merge is performed automatically.

### G3 — Evidence and claim provenance

A supplier statement must remain a CLAIM unless authority/evidence rules promote it.

PASS criteria:
- source and evidence references are preserved;
- extracted numeric values retain original units and source locator;
- unsupported claims cannot become FACT by repetition;
- contradictory evidence can coexist without destructive overwrite.

### G4 — Numeric / unit / model sanity

Before comparing a claim with a canonical requirement, normalize units and validate model identity.

PASS criteria:
- MPa/bar conversion is explicit and testable;
- throughput units cannot silently switch between pipe/min and pipe/hour;
- currency/value fields cannot lose currency;
- model aliases cannot be treated as equal unless identity evidence supports the mapping;
- impossible or out-of-range values are quarantined for review.

### G5 — Supersession and staleness

A newer event may supersede an older state without deleting history.

PASS criteria:
- `waiting_for_reply` becomes inactive when a qualifying reply is ingested;
- old claim remains queryable as historical evidence;
- active read-model returns only the latest valid state unless history is requested;
- stale-state regression test passes.

### G6 — Decision trace

A decision must be reconstructable from requirements, claims, contradictions, unknowns, and evidence.

PASS criteria:
- decision record lists supporting and contradicting evidence refs;
- unknowns remain explicit;
- recommendation cannot erase dissenting evidence;
- project authority source is recorded.

### G7 — Human approval boundary

Research, reading, analysis, drafting, and tests may proceed autonomously. Any external message, purchase, payment, contract, deployment, production-access change, destructive operation, or protected merge requires exact approval.

PASS criteria:
- outbound action without approval is denied;
- approval digest binds project, action, target, and exact parameters;
- changed payload invalidates prior approval;
- expired approval fails;
- denied approval cannot later be consumed;
- approved action is single-use.

### G8 — Replay / idempotency / partial failure

Consequential action must not execute twice under retry, race, or partial failure.

PASS criteria:
- same action digest cannot produce duplicate execution;
- approval consumption is atomic;
- crash after external-side success but before local acknowledgement is detectable and reconciled rather than blindly retried;
- concurrent workers cannot both execute the same approved action.

### G9 — Audit integrity

PASS criteria:
- every consequential transition appends an audit event;
- audit hash-chain verification passes;
- tampering with a historical row causes verification failure;
- event correlation allows reconstruction of the full case.

### G10 — Outcome and learning governance

PASS criteria:
- action outcome is recorded independently from the recommendation that caused it;
- lessons are candidate changes only;
- no prompt/rule/code change can self-promote from a metric alone;
- promotion requires experiment evidence, regression reference, rollback plan, and human gate when policy requires it.

## Adversarial regression suite

Minimum required scenarios:

1. Wrong supplier association.
2. Ambiguous alias collision.
3. Same contact used by two companies.
4. Cross-project attachment contamination.
5. Superseded supplier claim remains incorrectly active.
6. Waiting state remains active after reply.
7. Supplier claim promoted to FACT without authority.
8. Price without currency.
9. Pressure expressed in bar compared directly to MPa.
10. Throughput pipe/min misread as pipe/hour.
11. Similar but different machine model merged.
12. Attachment belongs to a different message/thread.
13. Approval generated for one recipient but used for another.
14. Payload changes after approval.
15. Approval expires before execution.
16. Approval denied then replayed.
17. Two workers consume one approval concurrently.
18. External action succeeds but local write fails.
19. Same external action retried after timeout.
20. Audit row tampered.
21. Old source with newer ingestion timestamp beats newer evidence incorrectly.
22. Duplicate outreach generated from two concurrent workflows.
23. Unsupported price copied between projects.
24. Lesson auto-promotes a prompt/rule change without review.
25. RLS or authorization configuration allows unintended table access.

## Supabase security hold

Current production write posture remains HOLD until access policies are explicitly designed and verified. `RLS enabled` without policies is not sufficient evidence of a production-ready authorization model.

Before production writes:

1. define actor/role/ownership model;
2. define RLS policies per table or move internal-only data to a non-exposed schema;
3. run Supabase security advisors;
4. test authorized and unauthorized reads/writes;
5. verify no service-role secret is exposed to clients;
6. document rollback.

## Implementation rule

Do not create a new subsystem when an existing primitive can be extended. The implementation delta should prefer adapters/projections around current `AuditLog`, `ApprovalStore`, identity tables, evidence tables, and project links.

## Maturity gates

- DESIGNED: this specification exists and is reviewable.
- IMPLEMENTED: code/schema changes exist on a non-production branch.
- TESTED: adversarial and regression tests pass with recorded evidence.
- MERGED: approved changes land in the protected target branch.
- DEPLOYED: approved deployment completes.
- PRODUCTION-VERIFIED: live behavior is independently checked after deployment.

No later maturity state may be inferred from an earlier one.
