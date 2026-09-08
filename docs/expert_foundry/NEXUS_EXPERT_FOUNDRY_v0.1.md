# NEXUS Expert Foundry v0.1

Status: IMPLEMENTED SCAFFOLD / NOT DEPLOYED / NO LIVE RESEARCH PROVIDER

## Purpose

NEXUS Expert Foundry is the governed system for building a research-led,
experience-aware and invention-capable digital specialist. Metallurgy and
chemical process engineering are the first proof domain; the knowledge model
is reusable across other domains.

The system does not claim to be universally superior to every expert. It must
earn bounded competence through blind evaluation against experts, primary
sources, plant measurements, laboratory results and reproducible experiments.

## Non-negotiable boundary

The Foundry may research, organize evidence, preserve experience, generate
hypotheses, propose experiments and draft inventions. It may not control
equipment, change a production recipe, authorize a trial, publish an invention,
contact a person, or promote knowledge without the applicable human approval.

## Operating loop

`QUESTION -> SEARCH LOG -> SOURCE -> CLAIM -> CONTRADICTION -> EXPERIENCE ->
HYPOTHESIS -> FALSIFICATION TEST -> EXPERIMENT -> RESULT -> EVALUATION ->
PROMOTION OR HOLD -> NEW QUESTIONS`

Every transition is recorded. Search failure, missing evidence and negative
results are retained because they change future research decisions.

## Nine record identities

1. `RESEARCH_RUN`: exact queries, providers, accepted/rejected sources, gaps,
   timestamps and stopping reason.
2. `CONVERSATION`: a chat locator and extracted records; always untrusted
   context and never authority by itself.
3. `SOURCE`: raw material before interpretation.
4. `CLAIM`: one bounded assertion linked to a retrievable source.
5. `EXPERIENCE`: tacit or operational knowledge tied to an observer, context,
   recurrence count, observed outcome and validation plan.
6. `HYPOTHESIS`: a proposed mechanism grounded in evidence or experience, with
   alternatives and a falsification test.
7. `EXPERIMENT`: a reviewable test design with variables, controls, measurement,
   acceptance criteria, hazards and stop conditions.
8. `RESULT`: observed output with raw-data locators, units and uncertainty.
9. `INVENTION`: a candidate combination of mechanism and implementation that
   still requires prior-art, feasibility, safety and experimental review.

## Scientific memory

Primary research, standards, patents, manufacturer documentation and plant or
laboratory measurements retain distinct source classes. A search result begins
as unverified material. Repetition by multiple AI systems does not promote it.
Applicability limits, operating context, contradictions, supersession and
uncertainty remain attached to every record.

## Experience memory

Experience is valuable without being silently treated as scientific fact.
Interviews, operator observations, maintenance records, failure reports and
shift practices enter as `EXPERIENCE / UNVERIFIED`. Independent observations,
historical production data and controlled tests may raise support. Conflicting
experience remains visible and produces a research question rather than being
averaged away.

## Research engine

Each run must preserve objective, scope, exclusions, query set, provider,
timestamps, returned and rejected results, source snapshots or locators,
extracted claims, contradictions, gaps, stopping reason, cost and the next
deterministic query. The engine actively searches for disconfirming evidence
and checks whether a source applies to the same material, equipment, process
window, geography and time period.

Research ingestion is append-only. A changed synthesis supersedes an older
one; it does not erase it. Backups are digest-bound and restore tests are part
of operational acceptance.

## Invention engine

An invention candidate must include the problem, proposed mechanism,
experience pattern, novelty hypothesis, expected benefit, failure modes,
required equipment, evidence for and against, prior-art search, experiment
plan, economics and current maturity. `IDEA`, `PRIOR_ART_SEARCHED`,
`SIMULATED`, `LAB_TESTED`, `PILOT_TESTED` and `REPRODUCED` are separate states.

## Evaluation

Competence is measured by factual and citation accuracy, calculation accuracy,
uncertainty calibration, diagnosis ranking, quality of falsification tests,
false-confidence rate, safety violations, novelty yield and measured process
improvement. Evaluation cases hide outcomes until predictions are committed.

## Integration with existing NEXUS work

- `research_evidence.py` remains the provider-neutral search/evidence boundary.
- `research_lab.py` remains discovery-run persistence and scoring plumbing.
- `task_handoff.py` and `coordination_kit.py` remain the private repo-backed
  exchange between AI roles.
- Expert Foundry adds the cross-domain knowledge/experience/hypothesis and
  promotion layer. It does not replace or duplicate those modules.

Those dependencies remain on separate feature branches at this checkpoint.
Integration must be performed only after their branch order and tests are
revalidated against the current `main`.

## Current guarantees and known gaps

The v0.1 code validates record classes, experience context, grounded and
falsifiable hypotheses, alternative explanations, structurally human-gated
promotion, append-only hash chaining, tamper detection and non-overwriting
snapshots.

It does not yet resolve references across records, enforce project/lane scope
across a graph, authenticate an approval ID against `ApprovalStore`, encrypt or
replicate backups, ingest chats, call a search provider, score expertise, run a
model, or schedule continuous research. A local hash chain detects accidental
or visible modification; without an external signed checkpoint it is not proof
against an administrator rewriting the entire history. These are explicit next
implementation gates, not capabilities implied by the scaffold.

## First acceptance proof

The first proof uses one bounded metallurgy problem and historical or synthetic
data only. It must demonstrate: source and search provenance; at least one
experience claim; a preserved contradiction; two alternative hypotheses; one
falsification test; an append-only chain; a verified snapshot; and a human-gated
promotion decision. No equipment or live production write is permitted.
