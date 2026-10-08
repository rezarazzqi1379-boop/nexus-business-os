# NEXUS Intelligence Platform: bounded sandbox proof

Maturity: IMPLEMENTED; focused tests passed; production/commercial outcome UNPROVEN.
Scope: synthetic SANDBOX / proof only. No commercial project ID is inferred.
Base: PR #105, c5ca95e1de808692296327c9835273ad6994ea7d.
Live GitHub CI observed 2026-10-08: tests run 37736488246, #1310, SUCCESS.
That success applies to the base, not this new commit.

## Recovery and authority gap

Read AGENTS.md, operator skill, project memory digest, current state,
docs/authority/AUTHORITY_STATUS.md and cross-chat bootstrap pointers.
Actual v1.8 Registry / v2.1 Master binaries are absent from this checkout and
the synced project sources. Pointers/reports name them but the authority record
still rejects their promotion. This remains UNKNOWN/CONFLICT; no claim of recovery
or canonical promotion is made. Available project master binaries cover Can Forming,
KCl/SOP, Heat Treatment and Hydrotester, but this generic sandbox consumes no specs.
Commercial use requires the exact source binaries, hashes, contradiction reconciliation
and a version-bound authority decision. Existing source files were not changed.

## Reuse decision and bounded primary-source comparison

Observed 2026-10-08. No package installed or activated. These are candidates,
not completed dependency audits or assertions that a version is vulnerability-free.

| Candidate | License | Fit | Security / maintenance evidence | Decision |
|---|---|---|---|---|
| Existing intelligence_graph, conversation_control, project_control_plane | repository terms; redistribution not assessed | project-scoped links, token allocation, bounded routing | existing tests exercised | reuse now |
| dlt core | Apache-2.0, distinct from commercial Hub terms | incremental REST extraction and merge | public security page reports no SECURITY.md; releases present; version-specific audit pending | next API adapter candidate, do not build generic ETL |
| DuckDB | MIT | analytical projection over existing evidence stores | documented security boundary warns that database files are not a security boundary; maintained releases | defer until measured analytical bottleneck |
| Scrapy | BSD-3-Clause | structured crawling | security/advisory and releases pages available; dependency audit and crawl permissions required | defer until API/native sources fail |

Sources:
- https://github.com/dlt-hub/dlt (core license)
- https://dlthub.com/docs/general-usage/incremental-loading
- https://github.com/dlt-hub/dlt/security
- https://github.com/dlt-hub/dlt/releases
- https://duckdb.org/faq
- https://github.com/duckdb/duckdb/security
- https://github.com/duckdb/duckdb/releases
- https://github.com/scrapy/scrapy/blob/master/LICENSE
- https://github.com/scrapy/scrapy/security
- https://github.com/scrapy/scrapy/releases

Architecture: authorized existing adapter -> scoped observation -> SHA256/version
change decision -> existing intelligence_graph candidate edge -> existing commercial
evidence/conversion gates. Existing hub remains persistence owner. No new orchestrator,
database, scheduler or parallel agents. Caller must revalidate freshness even on hits.
History is immutable tuples for this small proof; persistent indexing, deletions,
source cursors, HTTP ETags and field-level diffs remain unimplemented.

## Acceptance and measurements

Positive: changed content extracts; repeated bytes skip extraction; revisions retain
previous digest; candidate links retain source, origin and extractor version.
Negative: project/lane leakage, digest tampering and budget overspend are rejected;
extractor/origin changes invalidate cache; candidates never become verified demand.
Cheap/strong routing is policy-only, not a live model integration.

Allocator executed: 12,000 total policy envelope; history 1,000; evidence 3,500;
working 5,500; output 2,000. These are allocated limits, not measured session usage.
Synthetic three-observation test: two extraction decisions and one cache hit,
versus three naive extraction decisions (33.3% fewer decisions on this fixture).
No inference tokens or paid model calls in proof; whole-session/provider cost UNKNOWN.
Runtime retrieval cap tested: 3 queries / 100 estimated tokens; two consecutive
zero-qualified-yield observations stop further reservation. Estimates are not billing.

Focused command: Python -m pytest -q -p no:cacheprovider
tests/test_incremental_intelligence.py tests/test_intelligence_graph.py
tests/test_conversation_control.py tests/test_project_control_plane.py: 25 passed.
Regression: PYTHONPATH=src, PYTHONUTF8=1, Python -m pytest -q
-p no:cacheprovider tests: 1090 passed. Initial Windows default decoding caused
five text-contract failures; UTF-8 matches CI's Linux decoding and passes unchanged.
Python runtime reused from C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe;
no environment was installed or modified. Bundled runtime lacked pytest.

Control-plane plan executed with concurrency=1 and safe GitHub source;
no blocked/approval lanes. Catalog assignment is a planning result, not an active agent.
An initial unsupported lane was rejected; corrected to existing research lane.

## Next safe step and exact approval

Recover disputed binaries through authorized read access; reconcile before any
commercial vertical. Freeze a licensed API fixture and compare dlt incremental
loading against current adapter when its repeated cost is measured. Strong model
usage, factual freshness, commercial false-positive rate and live opportunity lift
remain UNKNOWN. No self-improvement adoption is claimed from one proof.

Local draft commit is authorized. Remote publication/new draft PR is not performed:
repository instructions require exact external-write scope, and non-Persian outbound
PR text requires owner review with Persian explanation. For new-commit CI approve
push of the exact commit to draft/nexus-intelligence-proof-2026-10-08 and an exact
draft PR payload/target. No merge, deployment, outreach, payment or sensitive changes.
