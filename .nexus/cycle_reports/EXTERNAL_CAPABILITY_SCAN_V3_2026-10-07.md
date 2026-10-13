# NEXUS External Capability Scan v3 — 2026-10-07

Status: RESEARCHED / NOT BLINDLY INSTALLED

## Admission rule
A public repository is not a capability. Admit only a mechanism that closes a measured NEXUS failure mode, survives overlap/security review, passes a local acceptance fixture, and improves conversion/quality/cost.

## Priority candidates

### CAP-ER-001 — Splink 5 probabilistic entity resolution
Source: moj-analytical-services/splink
Use: company/person/supplier alias resolution across transliteration, spelling and incomplete identifiers.
Decision: SANDBOX BENCHMARK NEXT.
Acceptance: known alias fixture recall improves over deterministic resolver with zero cross-company false merges.
Integration target: ENTITY_RESOLUTION → Steel Commercial Network.
No production install yet.

### CAP-EVAL-005 — agentevals offline trace evaluation
Source: agentevals-dev/agentevals
Use: score recorded OTel traces repeatedly without rerunning expensive agent calls.
Decision: SANDBOX BENCHMARK AFTER TRACE EXPORT.
Acceptance: detect wrong-tool/redundant-tool fixtures from one frozen trace and reduce eval re-execution cost.
Integration target: RED_TEAM / EVAL / OBSERVABILITY.
No external authority granted.

### CAP-TRADE-008 — Trade Graph / BACI structural intelligence
Source: Takshak-CS/trade-intelligence-module
Use: country-HS dependency, supplier exposure, substitution and cluster analysis.
Decision: PATTERN + DATASET STUDY.
Acceptance: reproduce one known bilateral HS flow from authoritative/raw dataset and expose source-year/HS-version; never treat 2024 historical flow as current demand.
Integration target: Trade lane → relationship hypotheses, not action readiness.

### CAP-FAIL-009 — Multi-agent failure attribution
Source: TraceElephant benchmark
Use: identify which agent/step made a failure inevitable.
Decision: PATTERN DONOR.
Acceptance: injected bad-source / wrong-tool / duplicate-search fixture correctly attributes failure stage.
Integration target: RED_TEAM root-cause taxonomy.

## High-overlap / HOLD
Deep-research DAG systems found in scan: useful patterns include frozen source snapshots, trace.jsonl, hard budgets, red-blue repair, evidence coverage and citation checks. NEXUS already owns orchestration; do not add a second orchestrator without measured superiority.

## Permanent discovery loop
DISCOVER → SOURCE SNAPSHOT → MECHANISM EXTRACTION → OVERLAP → SECURITY → FIXTURE → SANDBOX → ABLATION → REGRESSION → COST/CONVERSION DELTA → ADMIT/MERGE/HOLD/REJECT → CENSUS → CHECKPOINT.

## Safety
Trade-route analysis may find lawful alternatives. It must not conceal ownership, origin, destination, sanctioned parties, payment purpose or documents, and must not recommend sham intermediaries.
