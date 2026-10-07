# NEXUS CONTINUE v10.10 — LARGE-DIAMETER DEMAND RADAR + HEAVY-FORGING BUYER HUNTER

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: demand_geometry_router + regressions -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun.
NO EXPANSION ON RED CI.

MEASURED v10.9:
EVIDENCE_READY = 0.
Exact-grade buyer-side demand observations = 5.
Exact stock geometry/form matches = 0.
One high-value unresolved lead: PGO/Kuznia Glinik planned ~120,000 kg 42CrMo4 through end-2026, dimensions unresolved.

KEY LEARNING:
Generic grade-first search wastes budget on small bar/hex/channel demand.
EICO snapshot is predominantly LARGE-DIAMETER material.
Search geometry must move before expensive qualification.

MISSION:
Find demand whose geometry is structurally compatible with EICO snapshot/capability.

PHASE 1 — CI GATE.

PHASE 2 — LARGE-DIAMETER QUERY COMPILER
Generate grade+geometry+application searches around:
large diameter
heavy round
open-die forging
large shaft
rotor shaft
marine shaft
turbine shaft
mill roll
mandrel
crankshaft
large gear blank
heavy machinery shaft.
Use metric ranges compatible with each stock family.

PHASE 3 — GEOMETRY PREFILTER
Run demand_geometry_router before relationship/contact enrichment.
Reject:
wrong grade
wrong form
diameter outside snapshot
length outside snapshot.
Missing geometry -> FOLLOWUP_MISSING_GEOMETRY.

PHASE 4 — PGO 42CrMo4 DEEP DIVE
Resolve the planned ~120t 42CrMo4:
exact dimensions
form
delivery condition
heat treatment
testing
schedule
buyer unit
procurement status.
Do not infer from unrelated PGO tender items.

PHASE 5 — STOCK FAMILY LANES
Search separately:
20MnCrS5 Ø280-500
42CrMo4 Ø290-760
8620 Ø350-450
C15 Ø300-450
C45 Ø290-980
S355J2G3 Ø300-500
St52 Ø300-500
CK Ø100-980.
Do not collapse CK into a single exact grade when demand requires chemistry/standard.

PHASE 6 — HEAVY-INDUSTRY BUYERS
Prioritize:
open-die forges
shipbuilding/marine
power/turbine
steel mills
roll manufacturers
mining
cement
oil/gas
large gearbox
heavy press
large shaft/rotor repair.
Company capability != demand.

PHASE 7 — CURRENT BUY PROCUREMENT
Prefer 2026/late-2025:
RFQ
BUY_TENDER
purchase plan
maintenance shutdown procurement
award/protocol
import record.
Observation date governs currentness.

PHASE 8 — TECHNICAL FIT
After geometry passes, resolve:
standard
chemistry
mechanical properties
heat treatment
UT/NDT
surface/machining
certification
origin restrictions.
Grade-name match alone is insufficient.

PHASE 9 — STOCK RECONFIRMATION QUEUE
For geometry+technical matches:
mark SNAPSHOT_MATCH_RECONFIRM_STOCK until EICO gives fresh inventory confirmation.
No quotation availability claim.

PHASE 10 — COMMERCIAL CONVERSION
Keep four-layer gate:
relationship + demand + technical + currentness.
Inventory/geometry is an additional fit layer, not a replacement.

PHASE 11 — RED TEAM
Attack:
same grade -> same geometry
large component -> large raw bar
planned tonnage -> exact size
CK family -> exact grade
geometry match -> metallurgical equivalence
snapshot match -> available stock.
Every successful attack -> regression.

PHASE 12 — MEASURE
Primary:
geometry-compatible buyer demand/search.
Then:
technical-fit demand/search
EVIDENCE_READY/search
false-positive rejection rate
missing-geometry recovery
cost/latency.

OUTPUT:
large-diameter demand ledger
PGO 42CrMo4 dossier
stock-family buyer matrix
geometry rejection ledger
technical qualification queue
stock reconfirmation queue
conversion ledger.

PERSIST GitHub + Notion + Drive read-back.
Generate adaptive v10.11 from measured bottleneck.

NO OUTREACH.
NO PAID CREDIT.
NO MERGE.
NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
