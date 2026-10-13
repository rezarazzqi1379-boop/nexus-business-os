# External Capability Census v4 — Steel + Commercial GitHub Scan — 2026-10-07

Status: LIVE-VERIFIED METADATA + PATTERN EXTRACTION. No blind third-party runtime installation.

## CAP-TRADE-GRAPH-010 — ShahinHasanov90/trade-intelligence-graph
GitHub verification: public, not archived, Apache-2.0 stated in README; latest surfaced commit 2026-03-20 fixed CI/test expectations; repository is small and young (two surfaced commits).
Useful mechanism: declaration → entity resolution → graph → temporal/centrality/community analysis. For NEXUS retain importer/exporter/commodity/route relationship graph and evidence binding. Do not import fraud/evasion use cases as commercial routing logic.
Decision: SANDBOX_PATTERN + NATIVE_MINIMAL_IMPLEMENTATION.
Acceptance: project isolation; provenance-bound edges; reverse-buyer path fixture; duplicate-origin regression.

## CAP-AGENT-HEALTH-011 — opensearch-project/agent-health
GitHub verification: public OpenSearch organization repo, active surfaced commits in Sep 2026; large stack. Useful: golden-path trajectory comparison, cost/performance, OpenTelemetry traces, experiments, prompt/skill evaluation, underlying judge-model identity.
Decision: BENCHMARK_PATTERN, NOT FULL INSTALL YET.
Reason: high overlap with NEXUS telemetry/evals and substantial infrastructure cost. First adopt judge identity + trajectory comparison concepts natively; install only if ablation beats native path.

## CAP-TENDER-012 — sarva-20/ProcureX
GitHub verification: public, MIT added Feb 2026; tender PDF extraction → eligibility → market → strategy pipeline.
Decision: MERGE_PATTERNS, NOT AGENT_STACK.
Keep: tender input validation, structured requirement extraction, explicit eligibility/disqualifier stage. Reject duplication of four-agent orchestration unless benchmark proves gain.

## CAP-RFP-013 — dobtco/openrfps-scrapers
GitHub verification: latest surfaced commit 2014-10-03.
Decision: REJECT_RUNTIME / KEEP_SCHEMA_PATTERN.
Useful historical idea: normalize heterogeneous procurement pages into a stable JSON contract plus fixture-based scraper tests.

## CAP-NOUS-014 — OpenNous search candidate
GitHub verification of located open-nous/opennous-code: only surfaced init commit 2026-04-11 and README not found.
Decision: HOLD.
Search-derived claims about observation/entity/claim architecture are insufficient for runtime admission until the exact authoritative repository/docs are verified.

## Security rejection
A surfaced steel inventory/procurement repository explicitly mentioned hardcoded production credentials in a legacy component. Decision: REJECT_RUNTIME. Heat-number/mill-cert concepts may be studied independently; never copy credentials or unsafe integration patterns.

## New steel-native method
STEEL TRADE RELATIONSHIP GRAPH:
Importer/Buyer ↔ Supplier/Exporter ↔ Commodity/HS/Product ↔ Route ↔ Agent/Distributor ↔ Procurement Event.
Every edge carries project_id, evidence_ref and observed_at. Graph paths are discovery hypotheses; they do not establish current demand or compliance.
