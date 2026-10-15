# NEXUS Network & Opportunity Audit — 2 Sep 2026

Status: READ-ONLY MEASUREMENT + RESEARCH. Not canonical authority. No outreach, CRM write, payment, signup, merge, or deploy performed.

## Live internal measurements

- FACT — HubSpot company search returned 38 company records.
- FACT — HubSpot deal search returned 0 deal records.
- FACT — The existing company graph already spans the active NEXUS domains: hydrotester/OCTG equipment, KCl/potash, ferroalloys, industrial sourcing, and adjacent business contacts.
- MEASUREMENT — The main CRM gap is not raw company count; it is conversion of verified entities into project-bound opportunities/deals with evidence, owner, next action, freshness, and relationship route.

## Opportunity hypotheses — keep project lanes isolated

### PRJ-FAL-01 / FAL-B — Iranian ferrosilicon export

CLAIM / current external trade-data signal:
- Volza reported 172 observed Turkish buyers under HSN 72022100 across three years, with 19 active buyers in the last 12 months in the period shown on its 1 Sep 2026 page.
- Named high-activity Turkish buyers in the page include Kardemir Karabuk Iron Steel, Acarer Metal, and Iskenderun Demir Ve Celik.
- A separate current Volza global page lists 549 observed buyers under HSN 72022100 across 3,348 shipments.

Locators:
- https://www.volza.com/p/ferro-silicon/hsn-code-72022100/buyers-directory/buyers-in-turkey/
- https://www.volza.com/p/ferrosilicon/hsn-code-72022100/buyers-directory/

HYPOTHESIS — Turkey is a practical first buyer-discovery lane because current trade-data pages show recent buying activity and the NEXUS lane is specifically export-oriented. This is not proof of legal/payment/logistics feasibility or fit with the available Iranian FeSi grade.

Required acceptance before outreach:
1. verify buyer/import activity from a second source or direct company evidence;
2. verify exact FeSi grade/size/packaging against buyer need;
3. verify sanctions/payment/logistics feasibility;
4. identify a real relationship path or decision-maker;
5. bind the candidate to PRJ-FAL-01/FAL-B only.

### PRJ-HYD-01 — Hydrostatic tester

FACT / official supplier signal:
- Boyu Petro published an Aug 2026 hydrostatic-testing page describing single-, dual-, and multi-station OCTG hydrostatic-testing machines.

Locator:
- https://www.boyu-petro.com/270.html

CLAIM / secondary discovery signal:
- A current Baidu B2B ranking page lists multiple Chinese hydrostatic-testing-machine manufacturers. This is discovery evidence only and does not establish OCTG suitability, 120 MPa capability, or 60 pipes/hour performance.

HYPOTHESIS — if the existing GH/Marley/ANZ comparison does not close the pressure/throughput/FAT gates, a controlled rebid lane can be prepared using additional manufacturers, but only after the current vertical exits or is explicitly declared HOLD/rebid.

### Network conversion gap

MEASUREMENT — 38 HubSpot companies and 0 HubSpot deals indicates the CRM currently behaves more like a contact/company store than an opportunity operating system.

Recommended conversion model:
Signal -> Verified Company -> Project-bound Relationship -> Need Hypothesis -> Qualification -> Opportunity -> RFQ/Quote -> Deal -> Outcome.

Each promotion should require:
- project_id;
- evidence locator and freshness date;
- relationship route;
- role (buyer/supplier/OEM/integrator/referral);
- confidence class;
- blocker;
- next action;
- duplicate check;
- external-action approval class.

## Immediate high-value ideas

1. Build a project-isolated Relationship Route score: direct known contact > warm referral > verified decision-maker > generic inbox > unknown.
2. Add an Opportunity Promotion Gate so companies do not become deals merely because they exist in CRM.
3. Add a Dormancy/Recency rule: stale company/contact evidence cannot trigger outreach until refreshed.
4. Measure network quality by qualified paths, replies, referrals, quotes and gross-margin outcomes — not raw contact count.
5. Keep HubSpot as operational CRM; do not make it engineering or commercial authority.
6. Use trade-data platforms as discovery claims, then independently verify before outreach.

## Current blockers

- PRJ-NXO-01 production login health remains unverified until an exact build is deployed and tested in staging/production.
- Apollo credentials are currently invalid; do not depend on Apollo for network expansion.
- Granola account is not created.
- Supabase discovered project is inactive and not runtime-routable.
- FAL-B grade/lot traceability, destination, legal/payment/logistics feasibility remain unverified.

## Acceptance metrics for next network vertical

- zero cross-project entity promotion;
- zero duplicate outreach;
- 100% candidates with evidence locator + freshness;
- >= 2 independent evidence paths for shortlisted external companies where material;
- every promoted opportunity has a named relationship route and next action;
- no outbound action until exact recipient/payload approval.
