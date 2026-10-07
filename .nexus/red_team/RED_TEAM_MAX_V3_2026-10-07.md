# NEXUS RED TEAM MAX v3 — Adversarial Audit — 2026-10-07

## Gate
CI #1099 SUCCESS. evidence_conflict.py and its numeric-conflict regressions are TESTED.

## Scope audited
Opportunity Graph; Commercial Genome/outcomes; Country Opportunity Queue/leads; Trade/Evidence controls; State Drift; Lost Deal Autopsy; Experience Distillation/Memory; Agent Health; Capability Registry; Unified Data Environment; current sales-readiness and procurement/relationship controls.

## High-severity findings

### RTM3-01 — Country queue can rank compliance-uncleared sensitive-market opportunities
country_opportunity_queue.OpportunityCandidate contains compliance_ready but queue_score ignores it. A Russia/Belarus candidate can rank first even when compliance_ready=False. steel_country_leads blocks transaction_ready, but the ranking layer can still create misleading operational priority.
Safe fix: keep ranking informational, add an explicit executable/actionable gate rather than silently changing the score.

### RTM3-02 — Commercial Genome similarity ignores evidence freshness/contradiction
GenomeFeature requires evidence refs and observed_at, but similarity treats feature values as equally valid regardless of stale or contradicted evidence. This can create false comparables and contaminate historical outcome guidance.
Safe fix: evidence-aware comparable gate or adapter using existing freshness/triangulation semantics; do not duplicate evidence engine.

### RTM3-03 — Outcome aggregation lacks cohort/budget/time comparability
commercial_outcomes counts similar genomes but does not enforce same market period, search budget, source budget or stage exposure. It is safe as descriptive history but unsafe as causal strategy benchmark.
Safe fix: label descriptive-only unless a comparable cohort contract is supplied.

### RTM3-04 — Opportunity Graph verified state can drift after promotion
can_promote_verified checks current evidence at promotion time, but a persisted verified GraphEdge does not carry source-family/contradiction state itself. Later evidence drift requires external audit discipline.
Safe fix: connect verified-edge reads to state_drift/supersession rather than weakening promotion.

## Medium findings

### RTM3-05 — Agent health rewards evidence presence, not evidence quality
agent_health counts bool(evidence_refs), so low-quality or duplicated refs can improve score. Use only as operational health, not evidence-quality score.

### RTM3-06 — Capability registry is an older compatibility read-model
Activation vocabulary ACTIVE_LOCAL/EXPERIMENT_ONLY is not the same as project maturity IMPLEMENTED/TESTED/BENCHMARKED/INTEGRATED/ACTIVE/PRODUCTION. Do not use it to claim production maturity.

### RTM3-07 — Distillation case-count gate does not prove independence
experience_distillation requires >=3 cases for promoted knowledge but does not ensure independent source families/cases. Duplicate-root evidence could produce a false lesson.
Safe fix: add independence metadata only when a real caller can supply it; meanwhile keep promoted lessons evidence-review gated.

### RTM3-08 — State drift volatile-field coverage is incomplete
VOLATILE_FIELDS omits procurement status, award/winner, decision authority, readiness and relationship state. These are commercially volatile.
Safe fix: extend the existing field set and add regressions.

## Confirmed winning controls
- relationship-specific evidence binding prevents product overlap from becoming supplier relationship.
- sales_readiness fail-closes UNKNOWN/BLOCKED dimensions.
- evidence_conflict prevents secondary-source majority voting from resolving scalar conflict.
- procurement_fit prevents unsupported exact-fit promotion.
- lost_deal_autopsy keeps repeated observations as HYPOTHESIS until minimum context/evidence gates are met.
- distilled memory requires evidence and case count.

## False-negative / blind-spot risk
Strict relationship verification may miss true suppliers when public award protocols are inaccessible. Correct response is UNKNOWN/CANDIDATE plus targeted acquisition, not lowering verification threshold.

## Lost opportunities
ZVEZDA category-level recurring alloy/special-steel demand is a valid WATCH_FOR_NEXT_RFQ signal; absence of current award evidence must not erase the buyer from future monitoring. Belarus remains paused because measured information gain is low, not because market opportunity is disproven.

## Architecture / external-agent decision
No external Agent/MCP/framework is justified by these failures. The highest-value fixes are thin native gates around existing evidence, drift and readiness modules. Installing a new framework would add integration/security/maintenance cost without addressing the identified semantic failures.

## Promotion decision
PROMOTE: fail-closed readiness, relationship binding, numeric conflict handling, grade-vs-category recurrence separation.
ROLLBACK: none; no tested change demonstrated regression.
HOLD: causal use of Commercial Genome outcomes, compliance-unaware country ranking for execution, evidence-presence Agent Health as quality proxy.

## Commercial mission
Continue future-RFQ radar and relationship resolution after safe fixes. Commercial outcome remains UNPROVEN.
