# NEXUS Growth Discovery Census — 2026-10-07

## Newly useful mechanisms

### GROWTH-001 — Dual-time commercial evidence
Source clue: AuvaLab/ATOM (formerly iText2KG).
Novelty: preserve observation time separately from event validity time.
NEXUS use: prevent publication/scrape date from becoming procurement-event date.
Disposition: MERGE_PATTERN; implemented natively in pre_rfq_signals.py; no external runtime adopted.

### GROWTH-002 — Procurement-plan intelligence
Source: Kazakhstan public procurement developer services.
Novelty: query annual procurement plans, customers, participants, announcements and contracts as linked evidence, rather than waiting for tender listings.
NEXUS use: discover demand earlier; connect planned need -> buyer -> tender -> contract -> incumbent supplier.
Disposition: HIGH_VALUE_SOURCE; adapter research next. No submission/write action.

### GROWTH-003 — Signal clustering before RFQ
Source clue: industrial procurement practice research.
Novelty: combine weak dated signals (capex, expansion, hiring, supplier qualification/change, maintenance) instead of treating any one as proof.
NEXUS use: rank accounts for deeper evidence collection before public RFQ.
Disposition: IMPLEMENTED_PATTERN; requires live-source calibration before commercial promotion.

## Data principle
Store negative results and stale signals. Never silently convert historical shipment, publication date, hiring post, or company identity into current demand.
