# NEXUS Business OS

NEXUS is the control and learning layer for turning real business evidence into structured decisions and measurable outcomes.

## Current focus

The first coded vertical is **Procurement Signal-to-Outcome**:

`Evidence → Relationship → Signal → Opportunity → Outcome`

The goal is not to maximize architecture. The goal is to prove a closed loop on real commercial cases and only then automate or scale agents.

## Source-of-truth split

- **GitHub** — version-controlled code and technical specifications
- **Supabase/PostgreSQL** — structured runtime state
- **Notion** — human-readable operating context, canonical registry map, cross-AI handoff
- **Gmail** — primary evidence for live commercial interactions
- **Vercel** — deployment surface

## Operating rules

1. Designed != Implemented != Tested != Production.
2. No net-new agent/registry/framework unless an existing bottleneck justifies it.
3. Progress claims require retrievable evidence.
4. Consequential external actions remain human-gated.
5. Canonical objects receive writes; backup/snapshot copies are read-only.
6. Claude is used as an independent auditor/second opinion via the shared Notion handoff layer.

## Repository status

This repository is intentionally minimal. The first milestone is a small tested procurement vertical, not a large platform skeleton.
