# NEXUS CONTINUE v10.9 — STOCK-AWARE DEMAND HUNTER + EXACT-FIT PROCUREMENT

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: inventory_matcher + regressions -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun.
NO EXPANSION ON RED CI.

NEW HIGH-VALUE INPUT:
User-provided EICO capability sheet + ready-stock snapshot.

Snapshot inventory:
20MnCrS5 280-500mm / 3-10m / ~700t
42CrMo4 290-760mm / 2-7m / ~80t
8620 350-450mm / 3-7m / ~140t
C15 300-450mm / 3-8m / ~1141t
C45 290-980mm / 2-8m / ~156t
S355J2G3 300-500mm / 3-7m / ~419t
St52 300-500mm / 3-8m / ~64t
CK Series 100-980mm / 2-10m / ~1100t
sheet total ~3800t.

CRITICAL:
snapshot date not visible.
Stock currentness = UNKNOWN.
Never promise availability until reconfirmed.

MISSION:
Reverse the discovery flow:
STOCK/CAPABILITY -> exact buyer demand -> dimensional/grade fit -> relationship/currentness -> conversion.

PHASE 1 — CI.
PHASE 2 — EXACT-GRADE DEMAND SEARCH
Prioritize the listed stock grades and dimensions in buyer-side RFQ/tender/import/procurement evidence.
PHASE 3 — DIMENSIONAL MATCH
Match grade + diameter + length.
UNKNOWN currentness -> SNAPSHOT_MATCH_RECONFIRM_STOCK.
PHASE 4 — GRADE SEMANTICS
Do not treat Russian/European grade adjacency as equivalence without chemistry/mechanical/HT/standard evidence.
PHASE 5 — INVENTORY PRIORITY
Use tonnage as research-priority signal, not proof of current stock.
PHASE 6 — BUYER-SIDE DEMAND
Find exact buyers for high-stock families, especially C15, CK, 20MnCrS5, S355J2G3, C45, 8620, 42CrMo4.
PHASE 7 — APPLICATION MAPPING
Map each grade to evidence-backed component/application searches, then require buyer procurement evidence.
PHASE 8 — EXPORT + IRAN
Run both domestic and export lanes; evidence quality outranks geography.
PHASE 9 — CONVERSION
EVIDENCE_READY still requires relationship + demand + technical + currentness.
Stock snapshot adds fit evidence, not demand/currentness.
PHASE 10 — RED TEAM
Attack snapshot->current stock; grade name->equivalence; dimensional fit->sale; tonnage->availability; application->buyer.
Every successful attack -> regression.
PHASE 11 — OUTPUT
exact-fit demand ledger
stock-to-buyer matrix
reconfirmation queue
grade/application map
buyer-side procurement watchlist
conversion ledger
top commercial candidates.
PHASE 12 — SELF-EVOLUTION
Measure EVIDENCE_READY/search and exact-fit demand/search.
Generate v10.10 from measured bottleneck.

PERSIST GitHub + Notion + Drive read-back.
NO OUTREACH.
NO PAID CREDIT.
NO MERGE.
NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
