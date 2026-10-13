# Parallel Research Fabric v1

Goal: fan out independent research questions across the best available read-only adapters, then normalize, deduplicate, bind provenance and measure unique evidence yield before graph ingestion.

Pipeline:
MISSION -> DECOMPOSE -> ROUTE -> PARALLEL READ -> NORMALIZE -> PROJECT FILTER -> EVIDENCE FINGERPRINT -> DEDUPE -> CONTRADICTION CHECK -> ENTITY RESOLUTION -> METRICS -> GRAPH/CHECKPOINT

Rules:
- Parallel worker count is not a success metric.
- Same underlying evidence seen through two search engines counts once.
- Same claim from genuinely independent evidence may count twice and is preserved for corroboration.
- Cross-project results are discarded before merge.
- Protected workstreams are HOLD, never auto-routed.
- Missing preferred adapter may use an explicit fallback; silent substitution is forbidden.
- Adapter failure produces no evidence.
- Measure unique_evidence, duplicate_ratio, latency, cost and evidence_per_cost.
- Future routing may change only from measured performance, never popularity.

Maturity at creation: IMPLEMENTED, pending CI.
