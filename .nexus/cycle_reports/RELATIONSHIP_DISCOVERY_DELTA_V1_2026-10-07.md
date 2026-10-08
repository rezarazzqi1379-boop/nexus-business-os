# RELATIONSHIP DISCOVERY DELTA V1 — 2026-10-07
Status: LIVE PUBLIC RESEARCH / NO OUTREACH / NO PAID ENRICHMENT

## Adapter measurement
Apollo connector is reachable, but live read-only People API Search returned API_INACCESSIBLE on the current Free plan. No enrichment, credits, writes or outreach were used.
Decision: Apollo net-new person discovery = BLOCKED_BY_PLAN. Do not treat connector-connected as capability-available.

## RU-CHAIN-003 — RUSAL SAYANAL role binding
VERIFIED public procurement-role relationship:
Tatiana Aleksandrovna Shcherbak is named on multiple 2026 TenderPro procurement records for JSC RUSAL SAYANAL as Specialist, Material and Technical Supply Department and selection/procurement curator.
Independent event examples surfaced:
- electric motors SIEMENS tender id1227065 / later stage id1230971;
- spare parts/tools tender id1210293 / stage id1213493;
- welding materials tender id1172999.
Commercial graph edges:
RUSAL SAYANAL → HAS_PROCUREMENT_ROLE → Material & Technical Supply Specialist.
Tender events → CURATED_BY → Tatiana Shcherbak.
This is strong ROLE_BINDING evidence. It does not by itself prove she owns the chain category tender id1242233; chain-specific ownership remains UNKNOWN until the chain event itself binds the curator.
No outreach authorized.

## KZ-CHAIN-004 — Karcement maintenance role map
2026 public vacancy evidence binds Karcement to the role Engineer-Mechanic for repair of main and auxiliary technological equipment, with responsibilities for equipment operational readiness, maintenance, repair and planned preventive maintenance (PPR).
Commercial graph:
Karcement → HAS_FUNCTION → Equipment Maintenance / Mechanical Repair.
Maintenance role → INFLUENCES → replacement-part technical need [DERIVED].
This supports a technical-qualification route for chain/conveyor spares, but no named procurement owner is yet verified.

A public professional-search result surfaced a current Deputy Chief Power Engineer at Karcement. Keep as CLUE until directly verified from a suitable professional source; do not promote into procurement ownership.

## New relationship discovery hierarchy
1. PROCUREMENT_EVENT_PERSON: named curator/buyer on the actual tender/RFQ — strongest commercial role binding.
2. AWARD_RELATIONSHIP: buyer ↔ winner/incumbent from result/award.
3. TECHNICAL_EVENT_PERSON: named engineer/approver in technical clarification/specification.
4. ORG_ROLE: official management/org chart or current company role.
5. JOB_ROLE: current/recent vacancy proves a function exists, not the incumbent person.
6. PROFESSIONAL_PROFILE: useful person-role clue; verify company/currentness.
7. DIRECTORY_CONTACT: contactability only; does not prove buying authority.

## New network-growth searches
For each verified buyer:
A. repeat-event search by exact product/spec;
B. adjacent-spares search by same plant/site;
C. award/winner search;
D. tender curator/technical approver search;
E. vacancy/function search;
F. EPC/OEM relationship search;
G. supplier → other buyers reverse search;
H. standard/spec → other buyers search.
Every expansion preserves project_id, event date, evidence origin and state.
