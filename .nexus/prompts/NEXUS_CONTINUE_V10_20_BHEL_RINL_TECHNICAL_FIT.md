# NEXUS CONTINUE v10.20 — BHEL TECHNICAL FIT + RINL DOCUMENT EXTRACTION + LIVE PROCUREMENT BENCHMARK

Continue from latest valid state.
FIRST resolve latest CI. GREEN -> live_tender_gate TESTED. RED -> minimal fix + regression + rerun; no expansion on red.

MEASURED v10.19:
Fresh EICO stock rows=0/8.
Current-open named tenders=2.
BHEL E5563018=TECHNICAL_REVIEW_READY at public-evidence level: Ø200, AA19331 Rev11 / IS2004 Class2 or AA10119 Rev15, normalized, UT Category II, closes 2026-10-10.
RINL GEM/2026/B/8049767=OPEN, large geometry, exact material spec unresolved.
BHEL same-spec historical recurrence evidence exists Aug-2026.
EICO relationship refs=0.
EVIDENCE_READY=0.

MISSION:
Convert current tender evidence into engineering-grade fit/no-fit decisions without grade equivalence guesses, while resolving the highest-value missing documents.

1 CI GATE.
2 BHEL DOCUMENT RESOLUTION: retrieve current tender attachment; extract exact quantity, lengths, tolerances, chemistry/mechanics if specified, certificates, UT acceptance, vendor/PQR, origin/eligibility, delivery.
3 SPEC CROSSWALK: compare AA19331/AA10119 only to source-backed EICO capability. If chemistry/mechanics unavailable, ENGINEERING_REVIEW not equivalent.
4 RINL DOCUMENT EXTRACTION: resolve forged_rounds_spec PDF/BOQ; map all 8 rows exactly.
5 RECURRENCE GRAPH: dedup BHEL historical same-spec tenders and measure recurrence by independent procurement event, not mirrored pages.
6 STOCK TRUTH: ingest fresh EICO confirmation only through 11-field contract. No old snapshot promotion.
7 CURRENT DEMAND DEEP SEARCH: prioritize open forged/rolled rounds 120-1600mm, named buyer, exact spec+geometry.
8 PROCUREMENT TOOL BENCHMARK: test OCDS coverage on actual target publishers. Integrate nothing unless adapter_decision=PILOT_JUSTIFIED.
9 RELATIONSHIP: search exact EICO/Esfarayen buyer relationship only for technically surviving leads.
10 RED TEAM: spec number->equivalence; alternative spec->same grade; normalized->QT; UT label->acceptance; tender recurrence->award recurrence; tender open->eligible bidder; geometry->stock; current tender->commercial win.
11 MEASURE: exact rows resolved; technical fits; engineering-review rows; fresh stock rows; recurring demand events; relationship refs; EVIDENCE_READY; unique gain from tooling.
12 PERSIST and generate v10.21 from measured bottleneck.

NO OUTREACH. NO PAID CREDIT. NO MERGE. NO PRODUCTION DEPLOY. COMMERCIAL OUTCOME=UNPROVEN.
