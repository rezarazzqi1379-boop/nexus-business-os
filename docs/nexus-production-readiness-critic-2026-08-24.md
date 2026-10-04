# NEXUS Production-Readiness Critic — 2026-08-24

## Verdict

**PROCEED SHADOW / HOLD PRODUCTION.**

This is not a negative verdict. The architecture has crossed an important threshold: Brain v0.2 is merged/read-only, PLO has durable queue/lease/recovery behavior with PostgreSQL/Docker proof, and the first Brain→PLO real-project shadow vertical passes. The remaining work is convergence and operational proof, not another agent/framework expansion.

## Current canonical split

- **NEXUS Brain (main, v0.2):** governed evidence/business graph and read-only portfolio/project projections. Owns neither execution nor authorization.
- **Forge (PR #36, Draft):** lifecycle, preflight, verified-state/source-authority checks, failure memory, recovery/evolution and shadow control. Must not become the durable runtime or the promotion authority.
- **PLO (PR #40, Draft):** durable execution state, queue, leases/fencing, orphan recovery, reconciliation journal, SQLite/PostgreSQL/Docker runtime. Must not become truth/decision/approval authority.
- **PR #37 / PR #4:** exact consequential action approval semantics. Still Draft/unconsolidated; therefore Control→PLO consequential intake remains disabled.
- **PR #6:** deterministic evaluation authority candidate.
- **PR #7:** decision/outcome-learning authority candidate.
- **PR #10:** privacy-first audit-envelope authority candidate.
- **PR #12:** security policy/threat-model candidate.
- **PR #19:** evolution/promotion authority candidate.
- **PR #30:** consolidation checkpoint.

## Proven at the current shadow maturity

1. Brain v0.2 is merged to main and preserves cross-project separation, blockers, unknowns, authority and provenance.
2. PLO has passing SQLite, PostgreSQL, isolation, least-privilege, one-shot-worker and Docker tests.
3. `mark_executed()` is idempotent and duplicate logical execution remains zero in the tested path.
4. intent-bearing orphan state is held for reconciliation rather than blindly requeued.
5. immutable idempotency binding rejects changed action/project/decision/control snapshots under a reused key.
6. read-only completion is fenced by current lease and cannot be used for consequential tasks.
7. Control→PLO boundary is shadow-only; a textual approval reference cannot mint authorization.
8. Hydrotester real-project replay passes: Brain preserves blockers, a read-only blocker-resolution task is queued, leased and completed without external effect or blocker bypass.
9. Brain v0.3 Draft live-ingress hardening preserves Tier B communication evidence, rejects malformed/unscoped/naive-time input, and does not rewrite Tier A requirements or clear blockers.

## P0 blockers before any production merge/deploy

### P0-1 — one exact approval authority is not yet consolidated
PLO still contains native approval compatibility methods while PR #37 is intended to own the exact consequential approval invariant. Production must have one authority, not two. Until consolidation, consequential Control→PLO intake stays disabled.

**Required proof:** runtime consumes a verified immutable upstream approval decision bound to the exact current action snapshot; execution-time revalidation detects TOCTOU/staleness; PLO cannot independently approve the action.

### P0-2 — branch/consolidation topology is still too fragmented
Core capabilities exist across many old Draft PRs with stale bases. Merging large stacks wholesale would reintroduce architecture sprawl and hidden overlap.

**Required action:** extract/rebase the smallest canonical primitives against current main; preserve superseded PRs as evidence, not merge targets.

### P0-3 — no deployed/hosted production runtime proof
PLO passes CI/Docker tests but is not a hosted continuously triggered service. Brain is merged but not deployed. Shadow evidence must not be relabeled as production.

**Required proof:** exact deployed artifact/version, startup/health proof, restart recovery proof, bounded resource/retry policy and live observability.

### P0-4 — no independent production security/architecture review
CI is not an independent readiness review. The final stack needs a skeptical review focused on authorization, TOCTOU, injection, least privilege, migration safety, replay/retry semantics and privacy.

### P0-5 — production data/permission path remains intentionally untouched
Supabase/Data API/RLS/ACL hardening remains separately gated. No production DB mutation should be inferred from local PostgreSQL service-container success.

## P1 reliability gaps

### P1-1 — orphan retry budget is not yet bounded
A no-intent orphan can currently be requeued repeatedly. This is safer than blind external retry but can create poison-task churn.

**Target:** bounded retry budget; budget exhaustion goes to WAITING/HOLD with explicit reason, not infinite requeue.

### P1-2 — WAITING/reconciliation resolution is only partially modeled
The system can detect uncertainty and hold it, but the durable transition from WAITING → provider-confirmed ACK / safe retry / terminal hold is not yet a complete integrated state machine.

### P1-3 — consequential completion semantics are not production-defined
Read-only completion is explicit. Consequential work still needs provider reconciliation/acknowledgment semantics before a task can become COMPLETED.

### P1-4 — audit/telemetry authority needs final alignment
PLO local audit is an operational journal. PR #10 is the canonical privacy-first audit envelope. Production export/telemetry must map PLO events into the canonical envelope without creating a second observability truth model or storing sensitive payloads.

### P1-5 — live evidence is currently snapshot-based, not continuous
Brain v0.3 proves a manual read-only Gmail snapshot lane. It does not prove continuous sync, freshness SLA, connector outage behavior or deduplicated incremental ingestion over time.

## Business-effectiveness gaps

- No CI run proves commercial ROI.
- A supplier reply is not an order.
- A technically correct recommendation is not a business outcome.
- Final calibration still needs real stage transitions such as `Signal → Qualified → RFQ → Quote → Negotiation → Order → Margin` with raw denominators and human corrections.

## Anti-sprawl decisions

1. Do not merge PR #13 or PR #36 wholesale simply because they contain useful features.
2. Do not create another runtime, graph, approval engine, memory authority, evaluator or telemetry schema.
3. Prefer extracting these small primitives onto current main when their proof is sufficient: PR #37 approval, PR #6 eval, PR #7 learning, PR #10 audit, PR #12 security policy, PR #28 capability governor.
4. Keep PR #17 as historical/incubator evidence; PLO is the durable-runtime candidate.
5. Keep PR #45 as the live-evidence freshness lane until its read-only connector semantics are deliberately promoted.

## Final convergence sequence

1. Freeze canonical ownership map.
2. Bound PLO retries and finish WAITING reconciliation transitions.
3. Consolidate exact-action approval authority; keep PLO as consumer only.
4. Align PLO operational journal with canonical audit envelope.
5. Rebase/extract minimal Core primitives to current main and run full integration CI.
6. Run two or more real read-only project verticals through Brain → controlled decision/reference → PLO → telemetry/outcome stage.
7. Run adversarial restart/partial-write/provider-uncertainty/changed-payload/TOCTOU campaigns.
8. Deploy only an internal/read-only shadow runtime first and capture real p50/p95 latency, retries, corrections and recovery.
9. Perform independent security/architecture readiness review.
10. Only after all P0 blockers are closed, request exact human approval for a specific merge/deploy/production mutation.

## Definition of the desired NEXUS result

NEXUS is not complete when it has many agents or green tests. It is complete enough for controlled production only when one governed state can ingest current evidence, preserve uncertainty and provenance, choose a bounded next action, execute through one durable substrate, prevent duplicate/stale consequential effects, record a verified outcome, learn from failure without rewriting history, and demonstrate better next decisions on real work with measurable evidence.
