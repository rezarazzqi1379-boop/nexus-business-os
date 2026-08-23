# NEXUS Core Consolidation Plan v0.2

Status: REVIEW / PROJECT-WIDE FORGE CONSOLIDATION CHECKPOINT
Date: 2026-08-23

## Why this exists
NEXUS no longer has a capability shortage. It has an overlap, lineage, review, and promotion problem: many useful draft branches exist, several are intentionally superseded or integration-only, and multiple branches touch evidence, evaluation, learning, runtime, autonomy, and promotion semantics.

The project-wide rule is now the NEXUS Forge lifecycle:

`OBSERVE -> REVERSE ENGINEER -> RECONSTRUCT -> BENCHMARK -> BREAK -> DIAGNOSE -> IMPROVE -> INTEGRATE -> SANDBOX -> PROMOTE -> EXECUTE -> MEASURE -> LEARN -> EVOLVE`

Forge is a control policy, not a new agent framework. Existing canonical mechanisms must be reused before a new mechanism is created.

## Canonical ownership rule
Every cross-project concern must have one canonical owner. Other branches may consume, adapt, or experimentally replay the owner but must not create a competing source of truth.

Current ownership candidates:
- evidence semantics: PR #1
- requirement readiness: PR #2 plus newer authority semantics in PR #29 for Hydrotester
- capability/action routing and exact action-scoped approval: PR #4, with PR #18 security hardening to extract
- deterministic regression and promotion evidence: PR #6
- decision/outcome learning: PR #7
- privacy-first audit metadata: PR #10
- security policy/threat model: PR #12
- autonomy planning/runtime primitives: PR #13/#17 as incubators only
- evidence-driven evolution proposal/evaluation: PR #19
- authority/benchmark patterns: useful parts of PR #24, with Hydrotester authority superseded by PR #29
- capability adoption governor: PR #28
- Business Genome / opportunity / negative knowledge: PR #33
- public-pattern reconstruction/workforce experiment: PR #35
- Forge reconstruction-to-controlled-evolution contract: PR #36

## Core boundary

`Evidence -> Authority/Entity Resolution -> Decision -> Exact Action Approval -> Execution -> Outcome -> Learning`

Core owns only cross-domain invariants:
- provenance and epistemic-class preservation
- authority/supersession and immutable history
- project/entity isolation
- deterministic validation and fail-closed behavior
- exact-action human approval for consequential actions
- idempotency, duplicate-action, and no-op-write controls
- privacy-first compact audit metadata
- outcome-stage separation and measurement contracts
- versioned learning proposals that cannot self-promote

Domain-specific qualification remains in vertical modules.

## Project-wide Forge policy
Before any material new agent, workflow, project mechanism, connector wrapper, business engine, evaluator, or learning component:
1. OBSERVE the existing NEXUS capability and evidence.
2. REVERSE ENGINEER the mechanism and its owner.
3. RECONSTRUCT only missing behavior; do not copy hidden/private implementation claims.
4. BENCHMARK against the current baseline using explicit metrics and evidence refs.
5. BREAK with adversarial cases: stale authority, cross-project contamination, duplicate/no-op writes, malformed runtime values, approval drift, prompt injection, safety regression, partial failure, and missing outcomes.
6. DIAGNOSE root cause; do not weaken tests to make a branch pass.
7. IMPROVE the smallest responsible component.
8. INTEGRATE through existing canonical contracts.
9. SANDBOX / shadow replay before consequential execution.
10. PROMOTE only if required metrics improve and no safety regression exists; promotion eligibility is not deployment authorization.
11. EXECUTE only within the current authority boundary.
12. MEASURE actual outcome stage, not proxy success alone.
13. LEARN from observed success/failure with evidence.
14. EVOLVE through versioned proposals and regression protection.

## Failure policy
Recoverable isolated failures do not halt unrelated safe work. They become evidence-backed learning records and regression tests.

`isolated + recoverable -> continue unrelated safe work`

`consequential risk OR non-isolated failure -> contain affected action`

A failure record should capture component, failure mode, evidence refs, severity, root cause, correction, regression, and version fixed. Learning records are never authorization.

Observed Forge failure already converted into protection: PR #36 generated duplicate/no-op README writes during an update attempt. The project now treats byte-identical content writes as a preventable failure class and tests a no-op-write guard.

## Evidence / promotion anti-self-deception rule
Alignment with a human decision, CI success, responsiveness, a reply, an RFQ, or a quote is not a final business outcome.

PR #33 currently records 5/5 recommendation-human agreement across five real procurement observations, one reply-stage success, and zero final contract/order outcomes. Forge therefore must keep such evidence in EXPERIMENT/SHADOW rather than treating alignment alone as proof of commercial superiority or production readiness.

## Live Supabase re-verification
The earlier connector-permission-blocked wording is now stale for the current session. Live Forge verification on 2026-08-23 established:
- project `jhmhtrzhcpdfkoflnsac` is `ACTIVE_HEALTHY`;
- SQL reads succeed as `postgres` in `public`;
- 30 base `public.nexus_*` tables are present; 33 `nexus_*` relations appear in the wider information-schema/grant inventory;
- runtime state is populated, including 13 projects, 21 runtime-state rows, 2 lessons, 3 promotion gates, and 1 outcome;
- public PostgreSQL function count is 0.

Therefore PR #31's basic claim that the Supabase cross-project runtime exists is supported. Its individual state claims still require field-level verification before consequential use.

Security posture remains a separate concern: Security Advisor reports RLS-enabled/no-policy findings across many NEXUS tables. Direct replay shows RLS enabled with zero policies, while `anon`/`authenticated` retain broad grants on part of the relation set. This is currently fail-closed at the RLS row layer, not proof of leakage, but it leaves unnecessary latent authority. PR #16 now owns the least-privilege hardening proposal; no production permission mutation was applied in this Forge pass.

## PR disposition map

### KEEP / canonical candidate
- PR #1: explicit evidence classification.
- PR #2: requirement readiness shadow semantics; Hydrotester authority must use newer PR #29 lineage where applicable.
- PR #4: capability runtime and exact action-scoped gates.
- PR #6: deterministic evaluation + promotion evidence core.
- PR #7: bounded decision/outcome learning.
- PR #10: canonical privacy-first audit envelope; do not revive PR #11 as a second trace framework.
- PR #12: security policy/threat model candidate.
- PR #28: small deterministic capability governor; never an automatic production oracle.
- PR #29: current Hydrotester authority candidate preserving historical lineage.
- PR #31: cross-project integration/runtime documentation candidate; runtime existence now reverified, but runtime-sensitive fields remain evidence-bound.
- PR #33: Business Genome / opportunity / pattern-learning shadow engine; final-outcome evidence remains insufficient for promotion.
- PR #35: public-pattern reconstruction/workforce experiment; public behavior only, no claim of private implementation access.
- PR #36: Forge lifecycle/integration contract; remains stacked on PR #35 and must not duplicate PR #19.

### EXTRACT / keep only the useful invariant
- PR #18: exact per-send approval hardening -> extract to Core security.
- PR #24: extract A0-A8 authority, fail-closed supersession, maturity/benchmark, Can Forming scope-equivalence, and no-fake-precision rules; do not merge stale Hydrotester history mutation.
- PR #14: provenance-first research-mesh ideas only if a measured source-recall/quality bottleneck justifies them.
- PR #16: least-privilege Supabase hardening proposal. Live access and broad-grant/RLS posture are now reverified; production mutation remains HOLD pending dependency and ACL/default-privilege verification.

### INCUBATOR / do not expand as Core merge units
- PR #13: Autonomy Fabric. Preserve useful adapters/planner/checkpoint ideas; stop adding unrelated Core responsibility.
- PR #17: Autonomy Runner. Preserve bounded execution/idempotency/scheduler primitives; benchmark a real read/research loop before promotion.
- PR #19: evolution kernel. It is the canonical proposal/evaluation target for Forge learning, but remains non-production and human-gated.

### INTEGRATION-ONLY / DO NOT MERGE
- PR #9: compatibility shadow only.

### SUPERSEDED / HISTORICAL EVIDENCE
- PR #8: superseded evaluation experiment; PR #6 is canonical.
- PR #11: superseded trace experiment; PR #10 is canonical.

## Drift / overlap findings
1. Supabase runtime drift was reverified and resolved at the availability layer: current access is healthy. Security/least-privilege posture remains open under PR #16.
2. PR #13 and PR #17 contain valuable autonomy behavior but are too large/stacked to become Core merely because CI passes.
3. PR #24 contains useful benchmark/authority ideas but mutates stale Hydrotester lineage; PR #29 is newer for that domain.
4. PR #35/#36 are stacked experiments. Forge must not become a third capability/eval/learning registry.
5. Open-PR count itself is now a maintenance signal. Superseded/integration-only branches should not receive new features.

## Merge discipline
A candidate may be considered for Core only when all are true:
- one clear responsibility and one canonical owner
- source/authority semantics are explicit
- malformed input fails closed
- relevant adversarial tests exist
- no cross-project leakage
- no new implicit authorization path
- no-op/duplicate mutation is guarded where applicable
- exact CI evidence exists at the reviewed head
- no unresolved overlap with a smaller/newer canonical implementation
- outcome metric is appropriate to the claimed maturity
- runtime-sensitive claims are live-reverified
- rollback/reversibility is understood

## Immediate execution order
1. Use PR #30 as the project-wide disposition checkpoint and stop framework multiplication.
2. Keep PR #36 Draft and use it as the Forge contract; continue real shadow replays only.
3. Extract PR #18 exact-send approval into the eventual minimal Core.
4. Preserve PR #29 Hydrotester authority lineage; do not import stale PR #24 history mutation.
5. Treat PR #33 as outcome-learning shadow evidence, not ROI proof.
6. Treat PR #31's Supabase runtime-existence claim as reverified; keep field-level/runtime-sensitive claims evidence-bound.
7. Keep PR #16 as a hardening proposal only until dependency/ACL/default-privilege evidence is complete and exact production approval exists.
8. Keep PR #28 as a bounded governor and PR #19 as the existing evolution target; do not duplicate either.
9. Run future changes through Forge gates before adding new agents, registries, evaluators, or learning engines.
10. Promote hosted autonomy only after repeated real loops provide final-stage outcome evidence and safe-runtime proof.

## Non-goals
This consolidation does not authorize merge, deploy, external messages, permissions/access broadening, production database mutation, contracts/payments, or self-promotion.

The objective is fewer canonical mechanisms, stronger evidence, smaller review units, explicit lineage, and a system that turns observed failures into bounded improvements rather than either ignoring them or halting the entire platform.