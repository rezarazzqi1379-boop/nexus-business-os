# Commercial relationship vertical proof — 2026-10-13

Scope: SANDBOX / commercial-proof. EXPERIMENT_ONLY, fictional structured inputs.
No live buyer, sale, demand, compliance clearance or outreach authority is established.

## Continuity and audit

GitHub main observed through the connected read API on 2026-10-13:
`49ba5a0ca2b75dad61259fcdf3cce6246103957a`. The existing local mission is newer:
`caf79562197c24f6f061defb3c40a7f5031a9bdd`. Imported that committed local history
into this worktree and continued on `codex/intelligence-commercial-proof`.
The original checkout's modified live-proof artifact was not imported or modified.

Read project memory (SANDBOX), operating contracts and machine policy. Existing
allocator reserved history 1000, evidence 5000, working 14000, output 4000 tokens.
These are allocations, not measured session consumption. Agent-Reach preflight:
skip/local_work. Coordination plan used one build lane, no dispatched agents.

Audit findings:

- Ingestion: existing `Observation`, `Revision`, `ingest` retain hash lineage and
  suppress identical revisions. Optional pinned dlt adapter remains unchanged.
- Graph: `candidate_edge` produces hypotheses; `link(... verified=True)` trusts
  its caller. The new adapter supplies an exact, current trusted review boundary.
- Routing: existing read-only source routing and model policy are reused; this
  deterministic offline path requires no new provider or dependency.
- Budget: existing token allocator governs context; the adapter bounds input
  bytes before ingesting anything. Model tokens are zero; session usage unknown.
- Conversion: existing `current_demand_ready` could combine unrelated buyer,
  product and trigger edges. Fixed direct endpoint binding without changing its
  signature. It remains a low-level gate trusting its current/observed inputs;
  callers needing freshness, identity and review checks should use the adapter.

## Executable path and boundaries

`commercial_relationship_proof.prove_relationship` connects scoped source bytes
to existing incremental ingestion, hypothesis graph edges, deterministic JSON
claim extraction, legal-identity checking, hash-bound reviewer receipts, source
age/expiry checks, canonical publisher-family independence and the existing
commercial gate. Reviewed graph edges retain source URL/locator, digest, origin
and extractor version. Review metadata and identity mapping are trusted inputs
from an internal review store, never instructions or booleans from a source.

Only the exact buyer/product pair and current need relation can qualify. Name
similarity has no authority. Mirror URLs cannot create independent publishers.
Cross-project/lane and ambiguous revision batches fail before state changes.
The same digest is reviewed again for expiry on cache hits. Parser work is
counted even on a cache hit; extraction savings are not claimed.

The adapter returns research readiness only and rejects all other actions.
Live connector callers still need canonical reconciliation and recorded
`nexus_chat_bootstrap` preflight. This module is not an authenticated review
service or a general transaction approval gate.

## Reproducible measurement

Use an existing interpreter with project dev dependencies, with `PYTHONUTF8=1`
and `PYTHONPATH=src` on Windows:

```text
python tools/benchmark_commercial_relationship.py
python -m pytest -q tests/test_commercial_relationship_proof.py tests/test_steel_commercial_intelligence.py tests/test_incremental_intelligence.py tests/test_intelligence_graph.py
python -m pytest -q tests evals
python -m nexus_checks --transmission --state
```

Benchmark executes the actual baseline module from `caf7956` via `git show`.
Artifact: `data/research/commercial-relationship-benchmark.json`, including
baseline module hash, case decisions, evidence hashes and the resulting graph.

Eight synthetic cases: decision accuracy 3/8 baseline versus 8/8 candidate;
false acceptances 5 versus 0. True accepted relationships stay 1/8, so no yield
increase is claimed. Precision of accepted relationships: 1/6 versus 1/1.
Structured extraction: 8/8 exact fields. Model tokens: 0 for both paths.
Provider/session token usage unknown. Corpus is intentionally small, reuses
regression fixtures and is not held out; these figures do not estimate market
performance or unstructured extraction accuracy. Real commercial outcomes: 0.

First full run: 2376 passed, 5 failed because Windows default decoding misread
UTF-8 prompt files. All seven affected prompt tests pass with `PYTHONUTF8=1`.
No prompt policy was edited to accommodate those environment failures.
Final regression evidence is saved in `data/research/commercial-regression.txt`.
Final UTF-8 full regression: **2382 passed**, one upstream Starlette deprecation
warning, 75.35 seconds. This is local verification, not GitHub Actions success.
The measured exercise and bounded owner-decision cycle are recorded in the
existing UnifiedDataHub and `data/research/commercial-self-use.json`. Exercise
remains PARTIAL because live commercial evidence and remote CI are unresolved;
no procedural learning or production promotion was generated.

## Remaining gates and rollback

Canonical Registry/Master binaries and version conflict remain unresolved.
No connector-backed commercial promotion or real demand assertion is made.
GitHub exact-commit CI needs publication of the development branch and a PR
or workflow dispatch; no remote write is inferred from local commit authority.
No merge, deployment, payment or third-party contact occurred.

Rollback: revert this task's commit. Parent mission and optional dlt runtime
remain intact. The adapter is additive; the sole existing behavior change is
rejecting unrelated endpoint combinations in the demand gate.
