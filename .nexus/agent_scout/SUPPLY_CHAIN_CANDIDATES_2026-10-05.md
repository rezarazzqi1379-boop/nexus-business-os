# Agent Scout — Supply-Chain Chain-Discovery Candidates — 2026-10-05

State: DISCOVERED only. No repository installed, copied, executed, or activated.

## Current bottleneck
NEXUS v8.2 needs stronger multi-hop chain discovery, provenance-aware graph mutation, uncertainty-driven search, and entity resolution without introducing a second authoritative control plane.

## Candidates
### Helicase — Yunbo-max/Helicase
Potential pattern value: uncertainty-guided iterative search, specialized planner/search/reasoning/coding workers, deterministic graph mutation, stagnation-based stopping.
Adoption stance: PATTERN_ADAPTATION candidate, not installation. Public repo describes framework/preprint and says code by request, so executable adoption is not assumed.
Open questions: license/code availability, benchmark reproducibility, privacy/TOS of heterogeneous sources, overlap with NEXUS control plane.

### Preciso Supply Center — Preciso-GR/preciso-supply-chain-agent
Potential pattern value: evidence-backed proposed graph, validation before persistence, human review before durable graph mutation.
Adoption stance: PATTERN_ADAPTATION / possible INTERFACE candidate.
Open questions: license details, dependency/security review, benchmark against NEXUS evidence gate, whether human-approval persistence semantics fit non-production NEXUS experiments.

### OpenOSINT — OpenOSINT/OpenOSINT
Potential pattern value: statement-level provenance, append-only entity graph, non-destructive same_as deduplication and review queue.
Adoption stance: PATTERN_ADAPTATION candidate specifically for provenance/entity-resolution ideas; no security-research features are required for NEXUS commercial discovery.
Open questions: license/dependency review, source/TOS boundaries, overlap with existing entity/evidence modules.

### Neo4j Supplier Graph — neo4j-product-examples/neo4j-supplier-graph
Potential pattern value: supplier/BOM graph schema and GraphRAG examples.
Adoption stance: reference architecture only. It requires Neo4j/GCP/Gemini/BigQuery and would add substantial infrastructure complexity.
Open questions: measurable gain versus current lightweight graph primitives; cost/operational overhead.

## Scout decision
No candidate advances beyond DISCOVERED in this cycle. Highest-value next action is to benchmark patterns, not install agents. Candidate adoption must demonstrate measurable gain on the Belarus chain benchmark while preserving NEXUS evidence and attribution invariants.
