# NEXUS CONTINUE v10.14 — EVIDENCE DURABILITY + STOCK REFRESH BRIDGE

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: trade_recurrence_gate + regressions -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun.
NO EXPANSION ON RED CI.

MEASURED v10.13:
Independent shipment-bound 42CrMo4 recurrence at Ecuador buyer = 0 verified.
Visible duplicate Jan-29 rows = ONE_OBSERVED, not recurrence.
Previous DEW STAHLTRADE shipment-supplier binding = CLAIM_REVALIDATION_HOLD because current live refresh could not reproduce shipment-specific supplier evidence.
Named geometry-compatible buyer = 1.
EICO relationship refs = 0.
Current EICO stock evidence = INCOMPLETE.
EVIDENCE_READY = 0.

MISSION:
Make evidence reproducible before expanding commercial discovery, and bridge the only human-side blocker: fresh auditable stock confirmation.

PHASE 1 — CI GATE.

PHASE 2 — EVIDENCE DURABILITY
For every high-value commercial claim persist:
source locator
retrieved_at
observation key
raw claim
classification
independent-source count
supersession state.
A result that cannot be reproduced is CLAIM_REVALIDATION_HOLD.

PHASE 3 — TRADE DEDUP
Use trade_recurrence_gate.
Duplicate renderings of same buyer/date/HS/weight/product fingerprint = one observation.
Recurrence requires >=2 independent observations.

PHASE 4 — ECUADOR REVALIDATION
Search independent sources for:
Jan-29-2026 shipment supplier
additional distinct 42CrMo4/1.7225 large-round shipments
current RFQ/purchase plan.
Do not count page duplicates.

PHASE 5 — SUPPLIER ATTRIBUTION
Only restore a shipment supplier from CLAIM_REVALIDATION_HOLD when shipment-specific evidence is reproducible.
Aggregate top suppliers remain discovery-only.

PHASE 6 — FRESH STOCK BRIDGE
Prepare an internal confirmation payload for EICO covering:
observed_at
grade
standard
diameter
length
tonnage
condition
heat/lot
certificate
availability window
source owner.
Do not send externally without exact approval.
If user supplies confirmation, validate it against stock_evidence_contract.

PHASE 7 — BUYER DISCOVERY
Until evidence durability is stable, cap new buyer expansion.
Only add a buyer when named + geometry-visible + shipment-specific.

PHASE 8 — EICO RELATIONSHIP
Continue exact relationship search for verified buyers/suppliers.
No hit = UNKNOWN.

PHASE 9 — TECHNICAL ACCEPTANCE
For any surviving candidate resolve standard, HT/QT, chemistry, mechanics, UT/NDT, machining, certification and origin restrictions.

PHASE 10 — CONVERSION
EVIDENCE_READY requires durable/reproducible evidence for:
buyer
demand/currentness
geometry
technical fit
current stock
relationship.
No layer may rely solely on a non-reproducible claim.

PHASE 11 — RED TEAM
Attack:
duplicate rows -> recurrence
cached snippet -> durable evidence
prior-cycle claim -> current fact
top supplier -> shipment supplier
fresh verbal stock -> auditable stock
one import -> open demand.
Successful attack -> regression.

PHASE 12 — MEASURE
reproducible high-value claims / total high-value claims
independent shipment observations
shipment supplier bindings
current-demand refs
stock evidence completeness
EICO relationship refs
EVIDENCE_READY
false positives prevented.

OUTPUT:
evidence durability ledger
trade dedup ledger
Ecuador revalidation dossier
supplier attribution ledger
stock confirmation payload
buyer queue
conversion ledger
supersession ledger.

PERSIST GitHub + Notion + Drive with read-back verification where write authority is exact and available.
Generate adaptive v10.15.

NO OUTREACH.
NO PAID CREDIT.
NO MERGE.
NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
