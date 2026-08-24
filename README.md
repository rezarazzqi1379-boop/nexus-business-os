# NEXUS Business OS

NEXUS is a governed business knowledge-and-action layer for turning real evidence into structured decisions, controlled actions, measurable commercial outcomes and reusable learning.

## Current focus

The core commercial chain remains:

`Evidence → Resolved Entity → Signal → Opportunity → Next Action → Outcome → Learning`

NEXUS Brain adds a shared governed substrate beneath project verticals:

`Evidence → Claim/Requirement → Authority Check → Contradiction/Unknown Gate → Read-only Decision Projection`

The objective is not to maximize architecture, dashboards or agent count. New infrastructure must remove a measured bottleneck or improve a real workflow outcome.

## Current implemented Brain scope

**NEXUS Brain v0.2** is implemented, tested and merged to `main`.

It currently provides:

- governed graph primitives with provenance and authority tiers;
- explicit fact / claim / inference / unknown semantics;
- fail-closed contradiction and blocking-unknown gates;
- project isolation;
- read-only JSON project/portfolio projections;
- a dependency-free read-only HTML command surface;
- a four-project governed acceptance fixture covering Hydrostatic Tester, KCl, Heat Treatment and Can Forming.

Brain v0.2 is **not deployed and not production**. The command surface does not grant external-write authority.

## Source-of-truth split

- **Canonical project masters / Source Registry** — stable business and engineering authority.
- **GitHub** — canonical source for code, tests, CI and technical version history.
- **Gmail / Drive / official sources** — changing live evidence that must be refreshed before action.
- **Operational state systems** — current workflow state, always linked to evidence and never silently promoted to engineering authority.
- **ChatGPT / NEXUS HQ** — reasoning/orchestration/execution interface, not sole memory store.
- **Agents / APIs / orchestration** — execution layers, never authority by themselves.

## Operating rules

1. Designed != Implemented != Tested != Deployed != Production.
2. Facts and consequential relationships require retrievable provenance.
3. Supplier statements remain claims unless independently supported/promoted under authority rules.
4. Cross-project values never transfer merely because field names look similar.
5. Conflicts are retained and surfaced; they are not averaged or silently resolved.
6. Blocking unknowns fail closed for consequential use.
7. Consequential external actions remain exact-scope human-gated.
8. Uncalibrated heuristic scores are not probabilities.
9. Persistent graph/vector retrieval, GraphRAG and durable orchestration remain gated by measured need and separate test evidence.

## Validation state

- Brain v0.1 was merged through PR #41 after 70/70 regression tests.
- Brain v0.2 was merged through PR #42 after **81/81** pull-request CI tests on Python 3.12.
- The repository current-state manifest has been synchronized to 24 Aug 2026.
- Current Brain v0.2 code is not represented as a production deployment.

For the verified implementation state, hard gates and next proof target, read [`docs/architecture/current-state.md`](docs/architecture/current-state.md).

## Next proof target

Connect the read-only Brain projection to retrievable live operational state without production writes, then measure whether it reduces stale-source use, duplicate work and decision latency on real procurement loops. Only after that proof should persistent GraphRAG, durable orchestration or broader production infrastructure be promoted.
