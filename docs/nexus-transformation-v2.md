# NEXUS Transformation v2 — Canonical Decision OS

Status: SHADOW ARCHITECTURE / NOT PRODUCTION AUTHORITY
Effective design basis: 23 Aug 2026 canonical source set

## Target
NEXUS should operate as one evidence-governed Business Decision OS, not a collection of loosely coupled agents, chats, databases and PRs.

Primary business outcome chain:
Signal -> Qualified Opportunity -> Conversation -> RFQ -> Quote -> Negotiation -> Order -> Gross Margin -> Repeat Business

Control/evolution chain:
Sense -> Capture Claims -> Resolve -> Verify -> Test -> Understand -> Predict -> Match -> Decide -> Approve -> Execute -> Measure -> Learn -> Evolve

## Layer 1 — Canonical Authority
Stable authority is deliberately small.

- NEXUS Master Context v1.3: project-wide rules and architecture.
- NEXUS Source Registry v1.0: authority index and supersession rules.
- PRJ-HYD-01-ENG: Hydrostatic Tester Engineering Master v1.0.
- PRJ-KCL-01-ACC: KCl/SOP Acceptance Master v1.0.
- PRJ-HTL-01-ENG: OCTG Heat Treatment Engineering Master v1.0.
- PRJ-CAN-01-ENG: Can/Tube End Forming Engineering Master v1.0.
- ATF asset registry remains a production activation gap until approved binaries are hash-registered.

Quotes, emails, screenshots, audit packs, checkpoints, model output and web research are not canonical stable authority.

## Layer 2 — Evidence Plane
Preserve raw evidence and provenance. Dynamic facts must be refreshed before consequential action. Supplier claims remain claims until verified. No silent overwrite of originals.

## Layer 3 — Operational State
Projects, entities, contacts, tasks, blockers, next actions, opportunities and relationship states use stable IDs and must link back to evidence. Notion can remain a human-facing operational UI while all durable records stay portable to PostgreSQL.

## Layer 4 — Decision Packet
Every material decision should carry, at minimum:
- project_id
- canonical source refs
- current live evidence refs where needed
- claims / assumptions / unknowns
- contradiction refs
- relevant failure-memory refs
- decision ref
- outcome target
- approval class
- action/outcome refs when available

A decision packet does not become authority; it binds existing authorities into one auditable context.

## Layer 5 — Forge Preflight
Before material change or project action:
1. canonical owner check
2. failure-memory retrieval
3. source-authority check
4. project-isolation check
5. stale/live-evidence check
6. contradiction check
7. no-op/duplicate-write check
8. only then SHADOW_READY

SHADOW_READY never authorizes execution.

## Layer 6 — Execution & Approval
Internal read/research/classification can be increasingly autonomous after benchmark validation. External commercial, legal, financial, reputational or technical consequential actions remain exact-scope human approved.

## Layer 7 — Outcome Graph
Connect Evidence -> Decision -> Action -> Outcome -> Lesson. Do not confuse reply with order, quote with revenue, human agreement with commercial success, or CI green with production readiness.

## Layer 8 — Recursive Evolution
Generations are open-ended; every generation is bounded. Self-stop on safety regression, failure-rate excess, contradiction overload, architecture sprawl, budget exhaustion or marginal-gain plateau. Then audit, compare baseline/candidate, rollback or research-refresh as needed. Promotion still uses existing human gates.

## Four Canonical Project Locks
### PRJ-HYD-01
- OD approximately 89–180 mm.
- Up to 120 MPa only for relevant required duty points, not every geometry.
- Throughput approximately 60 pipes/hour.
- Pressure-size/end-condition envelope remains a required supplier qualification proof.

### PRJ-HTL-01
- API 5CT OCTG; OD approximately 63.5–177.8 mm; wall 2–20 mm; length 6–12 m.
- Quench + Normalize + Temper.
- Throughput approximately 40 pipes/hour.
- Never import Hydrotester throughput.

### PRJ-KCL-01
- Stable acceptance: moisture <=0.5%; water-soluble K2O >=61%; NaCl <=2%; MgCl2 <=1%; specified PSD; no visible black impurities; solubility >=99.5%.
- Quantity, buyer authority, permits, destination, price, payment, sanctions/logistics and supplier availability are dynamic and require refresh.

### PRJ-CAN-01
- Cylindrical can/tube approximately diameter 52–99 mm; necking/flanging/beading.
- Compare necking-only vs full-set where relevant.
- Final production rate, exact SKU geometry, mandatory operations and acceptance/tooling/support details remain open until buyer confirmation.

## Transformation Metrics
Project-level:
- stale-authority error rate
- cross-project contamination rate
- unsupported-claim rate
- duplicate outreach rate
- duplicate-state rate
- unresolved contradiction count and age
- human correction rate
- time-to-decision
- qualified opportunity -> quote -> order conversion
- gross margin and time-to-close when known

System-level:
- canonical coverage
- source refresh compliance
- failure-memory retrieval coverage
- regression escape rate
- architecture-sprawl rate
- rollback recovery success
- task-loss / false-completion rate

## Current Non-Negotiable Gaps
- ATF approved binary asset hashes are not yet production locked.
- Dynamic commercial facts must not be inferred from these stable masters.
- Open engineering unknowns in Hydrotester, Heat Treatment and Can Forming remain unresolved until fresh buyer/engineering evidence exists.
- KCl current purchase quantity/terms remain unverified dynamic state.
- Forge/Recursive Evolution remains shadow/unmerged until independent review and consolidation are complete.

## Design Principle
The transformation goal is not more agents. It is fewer ambiguous authorities, fewer duplicated state containers, stronger project isolation, better evidence retrieval, explicit contradictions, measurable outcomes and increasingly autonomous low-risk execution under bounded control.
