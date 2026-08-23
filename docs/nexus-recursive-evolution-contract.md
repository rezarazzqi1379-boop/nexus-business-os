# NEXUS Recursive Evolution Contract

Status: project-wide shadow architecture contract. This document does not authorize production execution, external sends, deployment, permission changes, financial actions, or self-promotion.

## Purpose

NEXUS may evolve across an open-ended sequence of generations, but no individual generation is allowed to run without bounded resources, explicit stop conditions, audit, comparison to baseline, rollback semantics, and recorded learning.

## Source authority prerequisite

Recursive evolution cannot manufacture authority. Before a material project change, stable requirements require the current Tier A canonical source for that project; explicitly dynamic points may use fresh Tier B live evidence. Tier C operational state cannot silently create stable requirements, and Tier D research/claims never govern until verified and promoted. Competing active canonical candidates, stale dynamic evidence or cross-project source use must block/hold before evolution proceeds.

## Canonical loop

EXPLORE -> BUILD -> TEST -> MEASURE -> LEARN -> CONTINUE

When a boundary is reached:

SELF-STOP -> FREEZE STATE -> AUDIT -> RED TEAM -> REGRESSION -> COMPARE TO BASELINE

Then exactly one of the following is selected:

- PROMOTE_RESTART: candidate passed independent audit and beats baseline; promotion still requires its existing human gate.
- ROLLBACK_RESTART: safety regression or failed independent audit; rollback the affected generation and restart from the prior accepted state.
- PLATEAU_RESEARCH_RESTART: progress is not meaningful or contradiction load requires refreshed evidence/research before another generation.
- SELF_STOP_AUDIT: a budget or quality boundary was reached; no further work in that generation until audit completes.

## Mandatory generation budgets

Every autonomous or semi-autonomous generation must have explicit ceilings for action count, cost units, runtime and retries. Additional domain-specific ceilings may be added, but these four may not be omitted for open-ended evolution loops.

## Mandatory self-stop triggers

A generation must stop for audit when any configured boundary is reached, including action/cost/time/retry budget exhaustion, safety regression, excessive failure rate, architecture sprawl, contradiction overload, or marginal improvement below the meaningful-gain threshold. Safety regression has priority over ordinary budget exhaustion.

## Project-wide applicability

This contract applies to Core / ControlPlane, Forge and preflight, Failure / Decision / Outcome memory, Evaluation and promotion evidence, Business Genome and opportunity discovery, research pipelines, agents and multi-agent workflows, connectors and automation runners, project-specific engines and future systems that claim autonomous or self-improving behavior. A subsystem may have stricter rules but must not weaken these invariants.

## Decision context

Where applicable, a material generation should carry a Decision Packet referencing project_id, canonical sources, current live evidence, claims/unknowns, contradiction refs, relevant Failure Memory, decision ref, outcome target and approval class. The packet binds existing authorities into an auditable context but never becomes authority itself.

## Failure semantics

Errors do not automatically halt unrelated safe work.

- isolated recoverable failure -> contain locally, record, learn, continue unrelated safe work
- consequential or non-isolated failure -> contain affected action/generation, preserve evidence, audit before restart
- repeated failure -> create or update regression coverage and relevant Failure Memory

A failure is not considered learned merely because it was logged. A future relevant change must be able to retrieve the lesson before implementation/promotion.

## Memory semantics

Evolution memory must support write -> manage -> read. At minimum, generations should preserve retrievable links among Observation -> Evidence -> Failure/Outcome -> Diagnosis -> Lesson -> Proposed Change -> Test -> Version. Stale or superseded memory should be marked, not silently deleted. Contradictory evidence must remain retrievable until explicitly resolved.

## Evaluation semantics

No single LLM judge may be the sole promotion authority. Promotion-critical evaluation should prefer deterministic regression tests, source/evidence verification, controlled interventions, reproducible metrics, and existing human gates where required. LLM judges may remain advisory.

## Anti-gaming invariant

A candidate may not improve its apparent score by weakening its own test, removing safety gates or source-authority rules, redefining success criteria after observing results, hiding failures, or dropping difficult cases from the benchmark. Changes to benchmark definitions require separate evidence and review.

## Autonomy invariant

Open-ended evolution is allowed across generations; unbounded execution inside one generation is not. The system must always retain a known accepted state suitable for rollback. Self-stop, audit and restart are normal operating states, not system failure.

## Promotion boundary

Recursive evolution never creates a new authority path. Decision/outcome evidence remains with existing owners; evaluation/promotion remains with existing evaluation/evolution owners; external action approval remains exact-action scoped; security policy remains separately authoritative; Forge orchestrates lifecycle and source/decision gates but does not grant itself production permission.

## Current implementation

Shadow implementation lives under PR #36 / Forge and is validated by adversarial tests for budget stop, safety rollback, failure-rate stop, architecture-sprawl stop, contradiction-triggered research refresh, plateau restart, independent audit, baseline comparison, source authority, project isolation and promotion human-gating.
