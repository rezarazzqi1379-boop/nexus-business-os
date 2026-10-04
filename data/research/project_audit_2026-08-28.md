# NEXUS Project Audit — 2026-08-28

Status: INTERNAL REVIEW. No production or external authority.

## Canonical baseline
- Active project-wide pair: Master Context v1.9 + Source Registry v1.6.
- Project masters remain isolated: PRJ-HYD-01, PRJ-KCL-01, PRJ-HTL-01, PRJ-CAN-01.
- Dynamic facts require live refresh before consequential use.

## Findings

### P0 — Architecture expansion outran measured vertical proof
FACT: Master Context v1.9 says the next promotion must be based on live evidence and measurable vertical acceptance tests, not architecture expansion.
CORRECTION: freeze net-new platform primitives unless they directly support a named acceptance test. Use Hydrotester as the primary vertical.

### P0 — Hydrotester operational state became stale on 28 Aug
FACT: earlier state said GH signed response was pending. Gmail now contains a new GH reply with a signed three-page technical confirmation and a newer Marley point-by-point response.
CORRECTION: treat the new replies as Tier B live evidence and replay qualification; do not preserve the old waiting state as current truth.

### P0 — GH signed response still does not close PO readiness
MEASUREMENT/CLAIM evidence in the signed attachment supports 120 MPa duty points and 60 pipes/hour at OD 168.3 mm / 120 MPa / 7 s hold.
MISSING EVIDENCE: one contractual pressure pass/fail rule; full capability matrix including grade and end condition; signed structural calculations/FEA with safety factor.
DEVIATION: only three mould sizes are included; extra sizes are priced separately, so complete tooling is not included at unchanged price.
PARTIAL: FAT and final scope are acknowledged, but detailed acceptance dossier and inclusion/exclusion reconciliation remain open.
DECISION: GH remains CONDITIONAL; not PO-ready.

### P1 — Open PR portfolio remains structurally risky
FACT: many historical PRs remain open/diverged. Green historical CI is not evidence of current architectural fit.
CORRECTION: continue selective-transplant policy; no bulk rebase/merge. Every new branch must identify canonical owner and measurable acceptance outcome.

### P1 — OpenAI live path must stay approval-gated
FACT: PR #78 hardens the boolean/key bypass and exact-head CI is green.
CORRECTION: do not activate live model execution until canonical single-use approval consumption is wired and API billing/runtime are verified.

### P1 — Production health is still not equivalent to deployment success
FACT: Railway deployment status can be green while login, WebSocket console and end-to-end app behavior remain unresolved.
CORRECTION: track deploy, health, login and live API verification as separate maturity/evidence fields.

### P2 — KCl remains commercial-refresh hold
UNKNOWN until refreshed: quantity/forecast, buyer authority, permit owner, destination, Incoterm, target price, payment route, sanctions/logistics feasibility and fresh supplier availability.
CORRECTION: no new commercial commitment from historical 1,200 MT/month.

### P2 — Can Forming remains engineering clarification
UNKNOWN: final geometry, mandatory operations, selected rate/CPM, acceptance test, tooling/changeover.
CORRECTION: do not promote GT3B64-NFBS-5 / D73 / 400 g references into canonical requirements without engineer confirmation.

### P3 — Heat Treatment remains paused
FACT: management pause governs. Throughput remains under revalidation hold.
CORRECTION: no supplier/RFQ restart; no Hydrotester throughput transfer.

## Immediate execution order
1. Replay latest GH + Marley live replies against Hydrotester master and decision pack.
2. Produce one normalized technical/commercial delta and PO-readiness decision.
3. Measure blocked unknowns and correction count; feed only tested behavior into FAT Generator/Opportunity Radar.
4. Keep PR #79 focused on this vertical proof; avoid further platform sprawl.
5. Resolve PR #78 separately under exact merge approval when needed.

## Acceptance criteria for next checkpoint
- latest GH and Marley states are not described as waiting if replies exist;
- no vendor becomes PO-ready with unresolved structural/FAT/tooling/acceptance gaps;
- latest Hydrotester evidence is project-isolated and source-located;
- no new architecture module is added unless tied to a measurable vertical test;
- exact-head CI is green before any merge proposal.
