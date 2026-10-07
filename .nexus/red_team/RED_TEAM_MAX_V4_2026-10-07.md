# NEXUS RED TEAM MAX v4 — Evidence-Native Commercial Adversary
Date: 2026-10-07

## Recovered authority
Source Registry v1.8 + Master Context v2.1 recovered before audit. Dynamic commercial facts require live refresh; memory/plugins are not authority; green CI is not deployment/business-value proof.

## Entry gate
CI #1151 SUCCESS on 11dd66e. trade_recurrence_gate + regressions are TESTED.

## Findings
RT4-01 HIGH — country_opportunity_queue ranks independently of compliance and previously had no explicit execution/actionability gate. Safe fix: actionable(candidate) requires compliance_ready while preserving informational ranking.
RT4-02 HIGH — Commercial Genome similarity validates evidence presence/date but does not exclude stale or contradicted features. Safe guard implemented in red_team_max_v4; direct integration into genome remains pending to avoid broad behavior change before regression evidence.
RT4-03 HIGH — commercial_outcomes counts comparable outcomes but lacks cohort/time/search-budget/source-budget/stage-exposure controls. Therefore descriptive only; causal strategy claims blocked by causal_benchmark_ready.
RT4-04 MEDIUM — experience_distillation case_count>=3 does not establish distinct cases/source families. Independent-distillation guard requires distinct case IDs + >=2 source families + evidence.
RT4-05 HIGH — prior v10.12 DEW supplier attribution demonstrated evidence durability failure: a prior-cycle commercial claim could not be reproduced and required supersession. Existing v10.13 supersession is correct; this becomes a permanent failure fixture.
RT4-06 MEDIUM — agent_health scores evidence presence, not evidence quality/freshness/contradiction. Do not interpret health score as evidence reliability.
RT4-07 MEDIUM — capability state labels are tool/runtime states, not NEXUS maturity states. Never map ACTIVE_LOCAL/AVAILABLE to TESTED/PRODUCTION.
RT4-08 CONTROL — Opportunity Graph already enforces fresh evidence for FACT/VERIFIED_EVIDENCE and triangulation for promotion; retain.
RT4-09 CONTROL — state_drift_audit volatile fields now cover stock, compliance, availability, provider health, CI, opportunity/procurement/award/authority/readiness/relationship; previous drift gap remains fixed.

## False positives / negatives / lost opportunity
False positives prevented: high queue score without compliance; stale genome similarity; duplicate cases distilled as knowledge; descriptive outcome counts treated as causal; non-reproducible supplier attribution.
False-negative risk: over-strict durability can suppress legitimate but single-source early signals. Mitigation: retain them as CLAIM/HYPOTHESIS/INVESTIGATE rather than delete.
Lost-opportunity risk: evidence gates must not erase candidates; ranking and actionability stay separate.

## Architecture verdict
No new agent/MCP/database is justified. The smallest effective mechanism is guards + regression tests on the existing branch.

## Maturity
country actionability fix: IMPLEMENTED / CI PENDING.
red_team_max_v4 guards: IMPLEMENTED / CI PENDING.
trade_recurrence_gate: TESTED via CI #1151.
No merge/deploy/production claim.

## Next
On green CI, integrate stale/contradiction filtering into Commercial Genome behind regressions, add evidence-quality-aware agent-health adapter, and make outcome benchmark labels explicitly DESCRIPTIVE unless exposure controls are present. Then resume v10.14 evidence durability + stock bridge.
