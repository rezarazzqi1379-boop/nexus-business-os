# Steel Capability Census v5 — MTC / Maintenance / Price Intelligence — 2026-10-07

## CAP-MTC-015 — GoSmarter-ai/mtc-extraction-benchmark
Verified GitHub: public, non-archived; latest surfaced commit 2026-03-19. Repository documents schema-first extraction of EN 10204 3.1 MTCs, OCR/LLM/vision comparison, JSON-schema validation, heat-level and mechanical/chemical evaluation.
Decision: SANDBOX_HIGH_PRIORITY. Native minimal intake schema installed first; no external OCR/LLM runtime copied.
Key adoption: certificate/date/standard/heat traceability, confidence-based routing, completeness review, ground-truth evaluation.
Boundary: extracted certificate data does NOT establish material compliance with a standard. Engineering/QA verification remains separate.

## CAP-MFG-GRAPH-016 — SainathPattipati/knowledge-graph-manufacturing
Verified GitHub: public, very small, two surfaced commits Feb 2026. README proposes Equipment/Component/Material/Process/Failure/WorkOrder ontology and graph reasoning. Performance/deployment numbers are unverified CLAIMS.
Decision: PATTERN_DONOR_ONLY.
Useful for sales: equipment → component → failure/replacement trigger → work order → spare part. Do not install Neo4j/GNN stack without measured need.

## CAP-MARKET-017 — Tksrivastava/autonomous-metal
Verified GitHub: public; surfaced commits through 2026-03-15. Focuses LME aluminum forecasting with macro/logistics/inventory features and chronological evaluation.
Decision: RESEARCH_PATTERN / NOT PRICE AUTHORITY.
Adopt concepts: chronological backtest, directional accuracy, feature attribution. Forecast output remains HYPOTHESIS and cannot replace live quoted/official market price evidence.

## New commercial method: Failure-to-Part-to-Buyer
For industrial sales discovery:
PLANT → PROCESS → EQUIPMENT → COMPONENT → FAILURE/WEAR MODE → REPLACEMENT PART → SPEC → MAINTENANCE/PROCUREMENT TRIGGER → BUYER ROLE → PROCUREMENT ROUTE.
This is stronger than company-directory search because it explains why and when a part is purchased.
