# NEXUS CONTINUE v10.13 — RECURRENT DEMAND PROVER + STOCK EVIDENCE CLOSER

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: stock_evidence_contract + regressions -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun.
NO EXPANSION ON RED CI.

MEASURED v10.12:
shipment-specific supplier bindings = 1.
Ecuador Jan-29-2026 shipment:
buyer = voestalpine High Performance Metals del Ecuador S.A.
supplier = DEW STAHLTRADE GMBH & CO KG.
42CrMo4 QT / 1.7225, forged pre-machined round, Ø400 x ~6m, 1,978kg.
EICO relationship refs = 0.
EVIDENCE_READY = 0.
Uzbekistan lane = PAUSE_LOW_INFORMATION_GAIN.

BOTTLENECK:
1) prove recurring/current large-forging demand;
2) close fresh EICO stock evidence;
3) only then evaluate commercial conversion.

MISSION:
Move from one shipment-specific proof to repeatable buyer demand and auditable sellable stock.

PHASE 1 — CI GATE.

PHASE 2 — ECUADOR RECURRENT DEMAND
Find additional shipment-specific 2025-2026 records for the same buyer and bind:
date, supplier, grade, HS, geometry, weight.
Do not count aggregate import totals as grade recurrence.

PHASE 3 — DEW RELATIONSHIP GRAPH
Research DEW Stahltrade as supplier:
large forged alloy product scope
producer relationships
other named buyers
42CrMo4/1.7225 shipment patterns.
Do not infer DEW is producer.

PHASE 4 — BUYER CLONES
Find named buyers with shipment-specific large 42CrMo4/1.7225 rounds compatible with EICO geometry.
Require buyer identity and visible geometry.

PHASE 5 — EICO RELATIONSHIP SEARCH
Search EICO/Esfarayen against Ecuador buyer, DEW, and new clones.
No evidence = UNKNOWN.

PHASE 6 — STOCK EVIDENCE CLOSURE
Use stock_evidence_contract.
Required:
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
Do not fabricate missing fields.
If no fresh internal evidence is available, output a precise human reconfirmation request, not a stock claim.

PHASE 7 — CURRENT DEMAND
A 2026 shipment proves recent procurement, not open demand.
Search RFQ, purchase plan, repeat shipments, tender, import recurrence or direct buyer procurement evidence.

PHASE 8 — TECHNICAL ACCEPTANCE
Resolve QT, EN/DIN standard, chemistry/mechanics, UT/NDT, machining allowance, certification, origin requirements.

PHASE 9 — CONVERSION
Require:
named buyer
current/recurrent demand
geometry
technical acceptance
current stock evidence
relationship evidence.
Only complete -> EVIDENCE_READY.

PHASE 10 — RED TEAM
Attack:
one shipment -> recurring demand
supplier -> producer
recent import -> open RFQ
snapshot -> current stock
buyer clone -> opportunity
DEW relationship -> EICO relationship.
Successful attack -> regression.

PHASE 11 — MEASURE
shipment-bound recurrence
named compatible buyers
current-demand refs
EICO relationship refs
stock evidence completeness
EVIDENCE_READY
false positives.

OUTPUT:
Ecuador recurrence ledger
DEW supplier dossier
buyer clone ledger
EICO relationship ledger
stock evidence completeness report
human stock reconfirmation checklist
current-demand watchlist
conversion ledger.

PERSIST GitHub + Notion + Drive read-back.
Generate adaptive v10.14.

NO OUTREACH.
NO PAID CREDIT.
NO MERGE.
NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
