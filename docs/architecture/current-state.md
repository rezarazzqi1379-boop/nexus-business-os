# NEXUS Current-State Architecture

Verified: 2026-08-24

This repository manifest records what is actually implemented/tested in code. It does not replace the canonical NEXUS Master Context, Source Registry or project engineering/acceptance masters. Dynamic commercial facts still require live evidence refresh before action.

## Current maturity

- **NEXUS Brain v0.1** — IMPLEMENTED + TESTED + MERGED through PR #41; historical implementation milestone.
- **NEXUS Brain v0.2** — IMPLEMENTED + TESTED + MERGED through PR #42; current Brain implementation layer.
- **PR #42 validation** — pull-request GitHub Actions passed **81/81** tests on Python 3.12.
- **Deployment** — Brain v0.2 is **not deployed and not production**. Do not infer parity with any existing Vercel/bootstrap surface.
- **Persistent graph / GraphRAG / durable execution** — research/design directions only; not implemented by Brain v0.2.

## Source-of-truth split

- **Canonical project documents** — stable business/engineering authority as indexed by the current NEXUS Source Registry.
- **GitHub** — code, tests, CI and technical version history.
- **Gmail / Drive / official sources** — changing live evidence; refresh before action.
- **Operational state systems** — must link to evidence and may not silently become engineering authority.
- **ChatGPT / NEXUS HQ** — reasoning/orchestration/execution interface, not sole memory store.
- **Agents / APIs / orchestration** — execution layers only; never authority by themselves.

## NEXUS Brain v0.2

Current governed portfolio slice covers:

1. `PRJ-HYD-01` — OCTG Hydrostatic Tester
2. `PRJ-KCL-01` — KCl / White MOP for SOP Feed
3. `PRJ-HTL-01` — OCTG Heat Treatment
4. `PRJ-CAN-01` — Can / Tube End Forming

Implemented capabilities:

- project-isolated governed graph records;
- Tier A/B/C/D authority separation;
- explicit epistemic states including fact, claim, inference and unknown;
- fail-closed provenance rules;
- contradiction detection for semantically comparable assertions;
- blocking-unknown decision gates;
- read-only JSON project/portfolio projections;
- provenance exposure in projections;
- dependency-free read-only HTML command surface;
- UI visibility for authority, epistemic state, blockers and contradiction radar.

The command surface is an implementation/operational interface. It is not a new authority source and grants no external-write authority.

## Canonical invariants covered by regression

### Hydrostatic Tester — PRJ-HYD-01

Current fixture preserves the controlling buyer basis from the engineering master: OD 89–180 mm, WT 6–20 mm, length 9–12 m, upper capability 120 MPa duty-dependent, hold 5–10 s, and buyer throughput basis 60 pipes/hour. Blocking unknowns remain visible for the signed critical-duty matrix and final FAT/TPI/ITP/pass-fail closure.

### KCl — PRJ-KCL-01

K2O acceptance minimum remains **61%**. The historical/reference **62% White Fine Grade A** preference is represented separately and cannot silently rewrite the acceptance minimum. Dynamic purchase quantity, permit/legal applicability and commercial route remain blocking unknowns until refreshed.

### Heat Treatment — PRJ-HTL-01

Stable process/dimensional requirements remain isolated from Hydrotester. The current working throughput of approximately 40 pipes/hour and the historical 40–60 pipes/minute engineer evidence are retained as conflicting evidence under a revalidation hold. No consequential use should treat either as newly resolved authority without buyer-engineering revalidation.

### Can Forming — PRJ-CAN-01

Necking-only and full-forming scopes remain separate. Golden Eagle speed statements remain supplier evidence/claims. Separate necking-only commercial scope, line-balancing compatibility and stable-speed FAT basis remain open blockers.

## Hard gates

1. No supplier selection merely because a fixture or brochure looks compatible.
2. No cross-project value inheritance based only on similar field names.
3. No fact or consequential relationship without retrievable provenance.
4. No silent resolution or averaging of conflicting values.
5. No automatic external outreach, contract, payment, publication or other consequential action from the Brain layer.
6. No production database migration based on remembered/guessed schema.
7. No claim that GraphRAG, durable execution or production deployment exists until separately implemented and tested.
8. Heuristic scores are prioritization aids, not probabilities unless calibrated against outcomes.
9. Designed, Implemented, Tested, Deployed and Production remain distinct maturity states.

## Observability direction

Future NEXUS agent/workflow observability should converge on structured operation, retrieval, tool-execution, workflow and evaluation events. Current OpenTelemetry GenAI semantic conventions are useful design input, but remain evolving guidance rather than NEXUS authority or a frozen telemetry contract.

## Next proof gate

Connect the read-only Brain projection to retrievable live operational state without introducing production writes. Measure whether the surface reduces stale-source use, duplicate work and decision latency on real procurement loops. Only after that evidence should NEXUS consider persistent graph/vector retrieval, GraphRAG, durable orchestration or a production deployment.
