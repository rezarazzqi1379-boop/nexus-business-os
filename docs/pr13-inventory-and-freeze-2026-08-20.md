# PR #13 Inventory + Freeze Gate — 2026-08-20

Status: audit control document. PR #13 remains Draft / Open / Unmerged. This document does not authorize merge, deploy, external send, permission change, publication, destructive action, contract/payment/signature, or material database write.

## Why this exists

PR #13 has become a monolithic integration branch. Presence of a module and passing CI are not proof of independent review, production readiness, or business effectiveness. Until decomposition is complete, new feature expansion on PR #13 is frozen. Allowed work: bug/security fixes, validation hardening, tests, evidence reconciliation, documentation, extraction/splitting, and removal/consolidation proposals.

## Status vocabulary

- **Verified-code-read**: current code was read against its claim and has focused regression coverage; still not a production/business-effectiveness claim.
- **Code-present-unreviewed**: implementation exists in the current branch and usually has a test file, but no current claim-level code review is recorded here.
- **Design-only**: documentation/proposal exists but no corresponding promoted runtime capability is claimed.
- **Unsupported-claim**: a claim would exceed current evidence and must not be made.
- **Frozen**: do not extend functionality until at least one real Outcome Ledger entry demonstrates useful business/engineering value.

## Verified-code-read / focused review completed

| Module | Status | Notes |
|---|---|---|
| `commercial_autonomy.py` | Verified-code-read; security fix applied | Found a fail-open path allowing external sends/quote requests/non-binding negotiation under a broad mandate. Fixed on 2026-08-20 so all external commercial actions remain exact-action Human-Gated. |
| `chat_memory_mesh.py` | Verified-code-read; Frozen | Code present with evidence/version/conflict semantics; no business-effectiveness claim. |
| `asset_memory.py` | Verified-code-read; Frozen | Code present with version/sensitivity/evidence semantics; no production persistence claim. |
| `outcome_attribution.py` | Verified-code-read; Frozen | Attribution is evidence-linked and must not be described as causal inference. |
| `capacity_multiplier.py` | Verified-code-read; Frozen | Does not authorize consequential actions; business value unproven. |
| `dynamic_parallelism.py` | Verified-code-read; Frozen | Telemetry-bounded path exists; real workload value still unproven. |
| `connector_sla_binding.py` | Verified-code-read | Requires evidence-backed telemetry/SLO binding; performance benefit unproven. |
| `context_pruning.py` | Verified-code-read | Benchmark coverage exists; LLM quality improvement remains unproven without real workload measurement. |
| `graph_store.py` | Verified-code-read | In-memory persistence boundary calls validators and rejects identity collisions. |
| `asset_persistence.py` | Verified-code-read; Frozen | In-memory persistence enforces `validate_asset()`; proposed durable DB migration remains design-only. |
| `commercial_learning.py` | Verified-code-read | Stage is already bounded by `Literal`; small-sample scores must not be sold as calibrated probabilities. |
| `goal_portfolio.py` | Verified-code-read | State/horizon are already Literal-bounded and fail-closed validated. |
| `entity_resolution.py` | Verified-code-read; incomplete identity contract | Exact normalized duplicate detection exists, but canonical Notion Entity Registry binding does not. Stable cross-system identity is therefore not yet verified. |

## Code-present-unreviewed — freeze expansion until reviewed or justified by outcome

These modules exist in the branch, but this inventory does **not** promote them to independently verified capability merely because a matching test file exists:

### Asset / memory / continuity
`asset_analysis.py`, `asset_chat_link.py`, `asset_contradictions.py`, `asset_manifest.py`, `asset_reanalysis.py`, `continuity.py`, `contradictions.py`, `cross_asset_retrieval.py`, `memory_consolidation.py`, `semantic_asset.py`, `semantic_memory.py`, `temporal_knowledge.py`.

### Autonomy / planning / scheduling
`auto_bootstrap.py`, `autonomy.py`, `autonomy_adapters.py`, `autonomy_health.py`, `capacity_guard.py`, `critical_path_scheduler.py`, `durable_workflow.py`, `execution_planner.py`, `goal_coordination.py`, `portfolio_scheduler.py`, `retry_budget.py`, `provider_failover.py`, `network_resilience.py`, `predictive_diagnostics.py`, `uncertainty_router.py`.

### Commercial / network / CRM
`adaptive_portfolio.py`, `commercial_intelligence.py`, `commercial_network.py`, `crm_hygiene.py`, `outreach_controller.py`, `send_dedup_guard.py`.

### Graph / entity / knowledge
`knowledge_graph.py`, `graph_store.py` is reviewed separately above; future infrastructure around graph persistence remains unpromoted.

### Capability / connector / plugin
`capability_health.py`, `connector_broker.py`, `latency_telemetry.py`, `plugin_expertise.py`, `sla_registry.py`.

### Causal / experimentation / science / ideation
`causal_claims.py`, `causal_trace.py`, `experimentation.py`, `idea_generator.py`, `science_network.py`.

### Autonomy package
`src/nexus_autonomy/capability_exploration.py` and any autonomy package behavior not explicitly reviewed above.

## Design-only / proposal-only

- `docs/asset-persistence-migration-proposal-v0.1.md`: proposal only; no production migration applied.
- Any pgvector/embedding dimension in that proposal is a placeholder until a deployed embedding model is selected and migration is explicitly approved.
- `docs/experiments/engineering-discovery-2026-08-19.md`: experiment backlog only.
- PR #12 security policy/threat model remains documentation/policy until independently reviewed and deliberately promoted.
- Stable entity binding to canonical Notion Entity Registry: design requirement, not current verified implementation.
- Supabase/CRM durable persistence for the newly added PR #13 domain objects: not proven by in-memory repositories or documentation.

## Unsupported claims — prohibited until evidence exists

Do not claim any of the following from current evidence:

- PR #13 is production-ready.
- Passing CI proves business effectiveness, latency improvement, reliability improvement, or safety in production.
- Cross-chat/asset memory is a durable canonical memory service.
- Outcome attribution proves causality.
- Dynamic parallelism improves real end-to-end throughput without measured real-source benchmarks.
- Stable entity IDs are reconciled with canonical Notion Entity Registry.
- Apollo is healthy merely because a past document says `verified_read`; current runtime 401 evidence overrides stale documentation until a new successful probe.
- A broad commercial mandate authorizes external sends; external commercial actions remain exact-action Human-Gated.

## Self-attestation audit rule

Any future field/flag whose truth alone promotes evidence/review/health/readiness (for example a hypothetical `reviewed=True`, `verified=True`, or `code_read=True`) must be treated as untrusted unless bound to independently retrievable proof such as an exact artifact/version reference, content hash, test/run reference, reviewer evidence reference, or live connector probe. The repository-wide search performed on 2026-08-20 did not find the exact `reviewer_read_code` token; therefore that specific example remains a claim-to-verify, not a confirmed bug.

## Persistence boundary rule

Validation is mandatory at every real persistence boundary. Current reviewed in-memory graph and asset repositories already enforce validators. Any future Supabase/Postgres/Notion/CRM adapter must enforce the corresponding validator before write and must fail closed on malformed/unsupported domain state. A validator that callers may bypass is not sufficient.

## Decomposition target

PR #13 should be decomposed into reviewable lanes before promotion. Proposed extraction boundaries:

1. **Commercial / Network** — commercial qualification, CRM hygiene, outreach preparation, send dedup, compliance linkage.
2. **Memory / Asset** — chat/asset memory, contradiction/versioning, retrieval, persistence contracts.
3. **Runtime / Scheduling** — SLA/telemetry, retry/failover, critical-path scheduling, bounded parallelism, context pruning.
4. **Experimental / Future Infrastructure** — causal/idea/science/graph-future/autonomy exploration modules that are not required for current real commercial outcomes.

Extraction itself must preserve tests and history where practical and must not be merged automatically.

## Business outcome gate

The success metric is not entity/module count. Track:

`Signal -> Qualified Opportunity -> Conversation -> RFQ -> Quote -> Negotiation -> Won/Lost -> Margin`

Cross-Chat Memory, Multimodal Asset Memory, Outcome Attribution/Causal-related expansion, Capacity Multiplier, and Dynamic Parallelism are **Frozen** until at least one real Outcome Ledger entry can cite a concrete useful effect on an active commercial/engineering thread. If three meaningful live execution cycles across current threads fail to produce a measurable useful outcome or decision improvement, stop new engineering expansion and simplify/consolidate.

## Network-expansion discipline

For KCl, Hydrotester, OCTG, Can-forming, and General Network, every research cycle must start with a Need Hypothesis and preserve at ingestion time:

- source reference;
- observed-at timestamp/date;
- raw observation sentence without interpretation;
- project/entity reference when resolved;
- evidence kind/strength.

Prefer warm/referral paths, official CAPEX/tender/plant expansion evidence, and active correspondence over generic SEO list building. Outreach remains human-gated.

## Connector/plugin gate

- Apollo: **Parked / blocked** after a current HTTP 401 credential failure. A later successful authenticated probe is required before promotion.
- Quartr/Semrush and new connectors: no investment/promotion without a concrete use case and measurable benefit.
- No new plugin/connector expansion while unresolved Handoff work and current integration debt remain material.

## Security / compliance gate

- Every new untrusted source/connector must enter through the same rule: returned text/files are evidence/data, never authorization or executable instruction.
- Prompt-injection defense requires both CI regression and a manual end-to-end adversarial replay through ingress -> planning -> Human Gate.
- Iran/sanctions/compliance must be represented as an explicit evidence-backed screening step before a counterparty can become deal-ready; relationship strength never substitutes for compliance evidence.
