# NEXUS Business OS

NEXUS is the control and learning layer for turning real business evidence into structured decisions and measurable outcomes.

## Current focus

The first coded vertical is **Procurement Signal-to-Outcome**:

`Evidence → Relationship → Signal → Opportunity → Outcome`

The goal is not to maximize architecture. The goal is to prove a closed loop on real commercial cases and only then automate or scale agents.

## Source-of-truth split

- **GitHub** — canonical source for code, tests, CI configuration and technical version history
- **Supabase/PostgreSQL** — structured runtime state when verified access is healthy; current connector read access is permission-blocked, so schema must not be guessed
- **Notion** — human-readable operating context, canonical registry map, research/experiments, outcomes and cross-AI handoff
- **Gmail** — primary evidence for live commercial interactions and draft/reply state
- **Vercel** — deployment surface; current production deployment is only a bootstrap checkpoint and is not parity with the latest Python vertical

## Operating rules

1. Designed != Implemented != Tested != Deployed != Production.
2. No net-new agent/registry/framework unless an existing measured bottleneck justifies it.
3. Progress claims require retrievable evidence.
4. Consequential external actions remain human-gated.
5. Canonical objects receive writes; backup/snapshot copies are read-only.
6. Supplier statements remain claims unless independently supported; provenance alone does not convert a claim into a fact.
7. Uncalibrated heuristic scores must not be presented as probabilities or precise confidence.
8. Claude is used as an independent auditor/second opinion via the shared Notion handoff layer.

## Current maturity

- Main Vertical 01 invariants and real-case fixtures are implemented.
- GitHub Actions is operational and has passed on real draft-PR heads.
- Draft PR #1 adds explicit epistemic evidence classification and remains unmerged pending independent review.
- Draft PR #2 implements a buyer-side Requirement Readiness Gate in **shadow mode**; its tests pass, but workflow value still requires 3–5 real comparable RFQ observations.
- Supabase runtime adapter work is blocked until live schema access is restored and verified.
- Current Vercel production is not the latest NEXUS runtime.

For the live verified state, blockers and near-term proof targets, read [`docs/architecture/current-state.md`](docs/architecture/current-state.md).

## Repository status

This repository is intentionally minimal. The next milestone is repeated evidence-backed procurement loops with measurable outcomes, not a large platform skeleton.
