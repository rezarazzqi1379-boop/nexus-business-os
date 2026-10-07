# NEXUS CONTINUE v10.15 — STOCK TRUTH CLOSER + DURABLE DEMAND CONVERTER

Continue from latest valid state.

FIRST resolve latest CI.
GREEN: Red Team v4 integrations + regressions -> TESTED.
RED: exact failure -> minimal fix -> regression -> rerun. NO EXPANSION ON RED CI.

MEASURED v10.14:
Reproducible Ecuador 42CrMo4 large-round observations = 1.
Independent recurrence = NOT_PROVEN.
Shipment-specific supplier binding reproduced = 0.
DEW attribution = CLAIM_REVALIDATION_HOLD.
Current-demand refs = 0.
EICO relationship refs = 0.
Current EICO stock evidence = INCOMPLETE.
EVIDENCE_READY = 0.

MISSION:
Close SELLABLE STOCK TRUTH first, then convert only durable buyer-side demand. Stop optimizing graph/discovery volume.

PHASE 1 — CI GATE
Promote only exact green-head behavior to TESTED.

PHASE 2 — STOCK TRUTH CLOSER
Validate fresh internal EICO confirmation against stock_evidence_contract. Required: observed_at, grade, standard, diameter, length, tonnage, condition, heat/lot, certificate_ref, availability_window, source_owner. Missing fields remain UNKNOWN. Never backfill from old snapshot.

PHASE 3 — STOCK DELTA
Compare fresh confirmation against undated snapshot. Record AVAILABLE_CONFIRMED / CHANGED / DEPLETED / UNKNOWN per exact grade-size-length row. Preserve old snapshot as historical evidence.

PHASE 4 — DURABLE DEMAND
Search only buyer-side evidence with reproducible locator + observation fingerprint: RFQ, buy tender, purchase plan, shipment/import, award, technical purchase specification. Duplicate renderings count once.

PHASE 5 — GEOMETRY FIRST
Only qualify demand intersecting confirmed current EICO geometry. Missing geometry -> FOLLOWUP_MISSING_GEOMETRY. Geometry failure -> reject before enrichment.

PHASE 6 — TECHNICAL ACCEPTANCE
Require standard, chemistry/mechanics where consequential, delivery condition/HT, UT/NDT, machining/surface, certification, origin restrictions. Grade name alone is insufficient.

PHASE 7 — RELATIONSHIP
Search EICO/Esfarayen relationship only for surviving named buyers. No hit = UNKNOWN. Never infer from intermediary or shared supplier.

PHASE 8 — CONVERSION
EVIDENCE_READY requires durable buyer identity + current/recurrent demand + geometry + technical acceptance + current stock + relationship evidence. Do not weaken gate.

PHASE 9 — RED TEAM
Attack fresh verbal stock->auditable stock; duplicate trade row->recurrence; intermediary->producer; top supplier->shipment supplier; same grade->technical equivalence; recent import->open demand; high score->actionable. Every successful attack -> regression.

PHASE 10 — MEASURE
current-stock completeness; confirmed sellable rows; durable buyer-demand observations; geometry-compatible demand; technical-fit demand; relationship refs; EVIDENCE_READY; false positives prevented; cost/latency.

OUTPUT:
FRESH STOCK LEDGER
STOCK DELTA LEDGER
DURABLE DEMAND LEDGER
TECHNICAL ACCEPTANCE QUEUE
RELATIONSHIP LEDGER
CONVERSION LEDGER
TOP SAFE NEXT ACTIONS.

PERSIST GitHub + Notion + Drive with read-back verification when connector write authority is available and appropriate.
Generate v10.16 from measured bottleneck.

NO OUTREACH. NO PAID CREDIT. NO MERGE. NO PRODUCTION DEPLOY.
COMMERCIAL OUTCOME = UNPROVEN.
