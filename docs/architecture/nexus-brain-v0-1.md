# NEXUS Brain v0.1 — Governed Business Graph

Status: IMPLEMENTED ON FEATURE BRANCH; NOT YET MERGED OR PRODUCTION

## Objective

Turn NEXUS from a collection of useful verticals into a governed knowledge-and-action layer without weakening existing authority, provenance, project-isolation or approval rules.

This is not a generic second brain and not a graph-visualization feature. The graph must be decision-bearing: every consequential conclusion must remain traceable to authority, evidence, project scope and unresolved blockers.

## Canonical architecture

`Raw Evidence -> Resolve Entities -> Claims/Requirements -> Authority Check -> Contradiction Radar -> Decision Context -> Next Best Action -> Approval -> Action -> Outcome -> Learning`

The graph is a shared substrate for verticals, not an autonomous authority. Agents and workflows may query it; they may not silently rewrite Tier A authority.

## Core node classes

- Project
- Company
- Person
- Product
- Requirement
- Claim
- Evidence
- Decision
- Action
- Outcome
- Opportunity
- Communication
- Connector
- Artifact
- Risk

## Authority tiers

- Tier A — canonical authority
- Tier B — live evidence
- Tier C — operational state
- Tier D — research / claims

Epistemic state is separate from authority. A supplier document may be Tier B evidence while the supplier's performance statement inside it remains a claim. Authority and truth are not synonyms.

## Required invariants

1. Tier A/Tier B nodes require retrievable source references.
2. Facts require provenance.
3. Consequential graph edges require provenance.
4. Project isolation is explicit; cross-project values are never imported merely because their fields are similar.
5. Conflicting active values are retained and surfaced, never averaged or silently reconciled.
6. Same-authority conflicts fail closed.
7. Blocking unknowns fail closed for consequential decision use.
8. Lower-authority evidence may challenge a governing value but cannot silently replace it.
9. Stale/superseded knowledge remains recoverable but is excluded from active decision context.
10. Graph visualization must display epistemic state and authority, not hide them behind generic confidence scores.

## First real vertical: PRJ-HYD-01

The Hydrostatic Tester is the acceptance vertical because it contains all important NEXUS failure modes:

- canonical buyer requirements;
- supplier capability claims;
- geometry/pressure dependence;
- throughput ambiguity;
- open FAT/pass-fail requirements;
- proposal evidence that is useful but not authoritative;
- possible conflicts between nominal machine rating and contractual duty.

Canonical buyer basis used by the fixture:

- OD: 89–180 mm
- wall thickness: 6–20 mm
- pipe length: 9–12 m
- maximum capability: 120 MPa, duty dependent
- hold time: 5–10 s
- buyer throughput basis: 60 pipes/hour

Open hold points remain blockers; the graph therefore must not select a supplier merely because one brochure advertises 120 or 150 MPa.

## Vertical acceptance questions

The implementation is useful only if it can answer, with provenance:

1. What requirements currently govern this project?
2. Which supplier statements are only claims?
3. What contradictions or lower-authority deviations exist?
4. Which unknowns block qualification?
5. Why is a supplier not yet selectable?
6. Which evidence supports the answer?

## Deliberate non-goals in v0.1

- no Neo4j dependency;
- no unbounded ontology;
- no autonomous supplier selection;
- no automatic external outreach;
- no probabilistic confidence theatre;
- no rewriting of current procurement verticals;
- no production database migration.

The v0.1 implementation is intentionally an in-process governed graph. PostgreSQL/Supabase persistence and GraphRAG should be introduced only after the invariants and retrieval questions are proven on real cases.

## Next build gates

1. CI/regression pass on this branch.
2. Load the real Hydrotester supplier matrix into graph records without weakening existing readiness rules.
3. Add a read-only `/v1/brain/project/{project_id}` API projection to the existing operator console.
4. Add a minimal graph UI showing authority tier, epistemic state, contradictions and blockers.
5. Repeat the vertical on KCl and Can Forming.
6. Only then evaluate PostgreSQL graph tables, vector retrieval and multi-hop GraphRAG.

## Definition of done for the pilot

- zero fact nodes without provenance;
- zero consequential edges without provenance;
- zero silent cross-project value inheritance;
- all known authority conflicts visible;
- buyer blocking unknowns prevent supplier selection;
- existing hydrotester readiness logic and tests still pass;
- operator can trace every displayed requirement/claim to retrievable evidence.
