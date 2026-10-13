# NEXUS Prompt Composition & Telemetry v1

Status: IMPLEMENTED / PENDING CI

## Precedence
ACTION_GATE > CANONICAL registry/master > PROJECT overlay > CAPABILITY > ADAPTER > SESSION.
Higher layer may constrain a lower layer. Lower layer may not override higher authority.

## Conflict policy
Never silently choose between equal-priority contradictory directives. Emit unresolved conflict and stop consequential execution. Cross-project project directives fail closed.

## Composition
Load only task-relevant layers. Progressive disclosure beats full-context stuffing. Every composed run records prompt IDs/versions, project ID, adapters, exact evidence references where applicable, and action-gate state.

## Telemetry
Measure success, failures, cost units and commercial conversion delta where meaningful. Telemetry is MEASUREMENT, not authority. A prompt variant is promoted only against a baseline and only when acceptance/regression remain green.

## Anti-Goodhart
Do not optimize a single score. A candidate cannot trade safety/project isolation/evidence quality for token cost, speed, lead volume or conversion. Protected-action gates are invariant.

## Rollback
Every promoted prompt keeps its previous tested version as rollback target. Failed/held variants remain in history with reason.
