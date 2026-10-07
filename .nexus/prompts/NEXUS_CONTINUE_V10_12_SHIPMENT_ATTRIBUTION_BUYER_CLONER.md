# NEXUS CONTINUE v10.12 — SHIPMENT ATTRIBUTION ENGINE + LARGE-FORGING BUYER CLONER

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: shipment_relationship_gate + regression -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun.
NO EXPANSION ON RED CI.

MEASURED v10.11:
named geometry-compatible buyer retained = 1.
shipment-specific supplier bindings = 0.
EICO relationship refs = 0.
EVIDENCE_READY = 0.
Uzbekistan geometry-compatible records remain BUYER_LOCKED.

CONFIRMED BUYER PROFILE:
voestalpine High Performance Metals del Ecuador S.A.
official role: specialty-steel/materials service center in Guayaquil.
Jan-2026 demand evidence: 42CrMo4 QT / 1.7225, forged pre-machined round, Ø400 x ~6m, 1,978kg.
Shipment supplier UNKNOWN.
EICO relationship UNKNOWN.
Open/current demand UNKNOWN.
EICO stock currentness UNKNOWN.

MISSION:
Solve shipment attribution and clone only evidence-rich large-forging buyer patterns.

PHASE 1 — CI GATE.

PHASE 2 — SHIPMENT ATTRIBUTION
For every high-value shipment, bind supplier only with shipment-specific evidence:
same date + buyer + product/HS + weight/geometry + origin or document reference.
Aggregate/top-supplier tables = discovery only.

PHASE 3 — ECUADOR RECURRENCE
Search 2025-2026 imports for the Ecuador entity:
42CrMo4
1.7225
722840
forged round
large diameter.
Measure recurrence, geometry distribution and supplier diversity.

PHASE 4 — BUYER CLONER
Find named specialty-steel service centers/importers with public shipments matching:
large forged alloy round
diameter >=290mm where visible
length 2-7m where visible
42CrMo4/1.7225 first.
Clone evidence pattern, not company description.

PHASE 5 — UZBEKISTAN RESOLUTION
Continue only high-information searches using exact date/weight/geometry.
If identity remains locked after controlled budget, PAUSE_LOW_INFORMATION_GAIN.
Never guess.

PHASE 6 — EICO RELATIONSHIP ATTRIBUTION
Search named buyers against EICO/Esfarayen aliases and shipment/project/reference evidence.
No hit = UNKNOWN.

PHASE 7 — FRESH STOCK EVIDENCE CONTRACT
Define a minimal evidence object for EICO stock refresh:
observed_at
grade
standard
diameter
length
tonnage
condition
heat_lot
certificate_ref
availability_window
source_owner.
Until populated, stock_current_refs stays empty.

PHASE 8 — TECHNICAL ACCEPTANCE
For geometry-compatible demand, resolve QT/HT, standard, chemistry, mechanics, UT/NDT, machining allowance, certification and origin restrictions.

PHASE 9 — RED TEAM
Attack:
aggregate supplier -> shipment supplier
recurring imports -> open demand
service center -> end user
same parent group -> same procurement
alias similarity -> same legal entity
fresh stock verbal claim -> auditable stock evidence.
Successful attack -> regression.

PHASE 10 — MEASURE
shipment-specific supplier binding/search
named geometry-compatible buyers/search
recurring geometry patterns
EICO relationship refs
stock-current evidence completeness
EVIDENCE_READY
false positives.

OUTPUT:
shipment attribution ledger
Ecuador recurrence dossier
large-forging buyer clone queue
Uzbekistan resolution decision
EICO relationship ledger
fresh-stock evidence contract/checklist
technical acceptance queue
conversion ledger.

PERSIST GitHub + Notion + Drive read-back.
Generate adaptive v10.13.

NO OUTREACH.
NO PAID CREDIT.
NO MERGE.
NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
