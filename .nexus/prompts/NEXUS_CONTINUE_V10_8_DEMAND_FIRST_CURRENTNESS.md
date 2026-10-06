# NEXUS CONTINUE v10.8 — DEMAND-FIRST PROCUREMENT BINDER + CURRENTNESS AUDITOR

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: currentness_engine + regressions -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun.
NO EXPANSION ON RED CI.

MEASURED RESULT:
v10.7 EVIDENCE_READY = 0.
Gate remains unchanged.

Repeated bottleneck:
relationship graphs exist,
technical/application signals exist,
but buyer-side DEMAND + CURRENTNESS are missing.

STRATEGY WEIGHT HYPOTHESIS:
40% DIRECT_BUY_PROCUREMENT
30% APPLICATION_PROCUREMENT_BINDING
30% MERCHANT_CUSTOMER_BINDING.

MISSION:
Find buyer-side evidence first, then attach technical fit and relationships.
Stop expanding broad merchant graphs until conversion improves.

PHASE 1 — CURRENTNESS AUDIT
Use observation date, not profile update date.
Classify CURRENT / RECENT / HISTORICAL / STALE.
Profile refresh never refreshes an old shipment.

PHASE 2 — BUY-SIDE PROCUREMENT HUNT
Search direct buyer/tender portals and documents for:
alloy steel bar
forged steel
round bar
shaft/gear material
roll/mandrel
heavy forging
mining/cement/steel/oil-gas/power components.
Require buyer-side demand semantics.

PHASE 3 — PROCUREMENT EXTRACTION
For each:
buyer
product
grade
standard
form
dimension
quantity
deadline
delivery
status
award
supplier
contact role
observation date.
No award -> CLOSED_UNKNOWN where closed.

PHASE 4 — IRAN APPLICATION BINDING
For technically relevant manufacturers, search:
raw-material tender
purchase notice
supplier list
certificate
project BOM/spec
import record
maintenance procurement.
Company product alone remains insufficient.

PHASE 5 — MERCHANT CUSTOMER BINDING
Spend merchant budget only on named downstream relationships.
No new generic sector expansion.
If no relationship-specific customer evidence, record zero.

PHASE 6 — CONVERSION
Join:
DEMAND
CURRENTNESS
TECHNICAL
RELATIONSHIP.
Only all four -> EVIDENCE_READY.

PHASE 7 — RED TEAM
Attack:
profile update -> current shipment
tender date -> still open
sale tender -> buy demand
technical manufacturer -> raw-material buyer
historical award -> current supplier
contact role -> award authority.
Every successful attack -> regression.

PHASE 8 — MEASURE
Primary: EVIDENCE_READY/search.
Also:
buyer-side demand refs/search
current observations/search
relationship bindings
technical fits
false positives prevented
cost/latency.

If EVIDENCE_READY remains zero:
do not lower gate.
Identify which missing layer dominates and adapt v10.9.

OUTPUT:
buy-side procurement ledger
currentness audit
Iran application-procurement ledger
merchant customer-binding ledger
conversion ledger
top evidence gaps
strategy-weight decision.

PERSIST GitHub + Notion + Drive read-back.
Generate adaptive v10.9.

NO OUTREACH.
NO PAID CREDIT.
NO MERGE.
NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
