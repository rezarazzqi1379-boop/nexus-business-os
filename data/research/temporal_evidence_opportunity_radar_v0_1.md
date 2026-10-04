# NEXUS Temporal Evidence + Opportunity Radar v0.1

Status: EXPERIMENTAL / INTERNAL. No external action or production authority.

## Problem
NEXUS needs to reason over facts that change over time without silently mixing stale and current values, and it needs a commercial/technology opportunity funnel that rewards evidence and reversibility rather than idea volume.

## Temporal evidence contract
- Preserve project IDs; never resolve one project's evidence with another project's values.
- Preserve epistemic class: FACT, MEASUREMENT, CLAIM, ESTIMATE, ASSUMPTION, HYPOTHESIS, UNKNOWN.
- A newer timestamp does not by itself supersede older evidence.
- Supersession must be explicit.
- Simultaneously active incompatible values return CONFLICT, never an invented reconciliation.
- Historical evidence remains retrievable after it is no longer current.

## Opportunity radar contract
Discovery -> Evidence -> Deduplication -> Validation -> Score -> WATCH / VALIDATE / EXPERIMENT / REJECT.

An opportunity cannot auto-promote from weak evidence. Capital-heavy or difficult opportunities must validate before experiment. Critical safety risk rejects. Every candidate requires a measurable acceptance test and rollback.

## First verticals to test after code-level acceptance
1. Installed-base retrofit/spares radar using public/sanitized signals.
2. Supplier-route resilience radar with no outreach.
3. Engineering FAT/test-plan opportunity generated from verified requirement gaps.
4. AI capability watch item promoted only after primary-source evidence and a frozen sandbox benchmark.

## Acceptance
- tests prove zero cross-project leakage;
- contradictory active values return CONFLICT;
- explicit supersession selects the intended current evidence while retaining history;
- weak-evidence opportunities cannot enter EXPERIMENT;
- duplicate opportunities fail closed;
- no code path sends messages, spends money, changes production, or grants authority.
