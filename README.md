# NEXUS Business OS

NEXUS is an evidence-governed Business Decision OS for procurement, engineering qualification, commercial opportunity discovery and controlled execution.

## Current transformation

The target shadow architecture is documented in [`docs/nexus-transformation-v2.md`](docs/nexus-transformation-v2.md).

NEXUS now treats source authority as a first-class control:

- `data/canonical_source_registry_v1_0.json` mirrors the current canonical authority set for deterministic validation.
- `data/canonical_project_requirements_v1_0.json` mirrors stable engineering/acceptance anchors and explicitly separates unresolved/dynamic fields.
- Forge project preflight blocks cross-project contamination, stale dynamic evidence, competing canonical sources and attempts to promote supplier/research claims into stable authority.
- material decisions can be represented as unified Decision Packets linking canonical sources, live evidence, claims, unknowns, contradictions, prior failures, outcome targets and approval class.

## Source-of-truth split

- **Canonical project sources** — stable approved operating/engineering/acceptance authority; deliberately small and explicitly versioned.
- **GitHub** — canonical code, tests, CI configuration and technical version history.
- **Supabase/PostgreSQL** — structured runtime state when live-verified. Current project status was re-verified as `ACTIVE_HEALTHY`; runtime claims must still be refreshed rather than inherited from historical checkpoints.
- **Notion** — human-facing operating context, recovery/checkpoint surface and structured working state where applicable; duplicate historical containers are not authority by name alone.
- **Gmail / Drive / official sources** — live evidence for changing commercial facts, proposals, threads and current counterpart state.

## Core operating chain

`Signal → Qualified Opportunity → Conversation → RFQ → Quote → Negotiation → Order → Gross Margin → Repeat Business`

Control/evolution chain:

`Sense → Capture Claims → Resolve → Verify → Test → Understand → Predict → Match → Decide → Approve → Execute → Measure → Learn → Evolve`

## Operating rules

1. Designed != Implemented != Tested != Deployed != Production.
2. No net-new agent/registry/framework unless an existing measured bottleneck justifies it.
3. Progress claims require retrievable evidence.
4. Consequential external actions remain exact-scope human-gated.
5. Canonical objects receive writes; backup/snapshot copies are recovery evidence, not authority.
6. Supplier statements remain claims unless independently supported; provenance alone does not convert a claim into a fact.
7. Dynamic commercial facts must be live-refreshed before consequential action.
8. Cross-project engineering values must never be transferred without explicit authority.
9. Uncalibrated heuristic scores must not be presented as probabilities or precise confidence.
10. Recursive evolution may continue across open-ended generations, but every generation is bounded, self-stopping, auditable and rollback-capable.

## Current maturity

Forge, Failure Memory retrieval, canonical-owner checks, source authority, project preflight, contradiction/outcome gates, Generation Ledger and Recursive Evolution are implemented in shadow branches/PRs and covered by CI. They are not production authority or autonomous self-promotion.

The current transformation objective is not more agents. It is fewer ambiguous authorities, fewer duplicated state containers, stronger project isolation, explicit contradictions, measurable outcomes and increasingly autonomous low-risk execution under bounded control.
