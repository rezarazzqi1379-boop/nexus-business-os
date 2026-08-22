# NEXUS Meta-Orchestrator Control Plane v0.1

Purpose: coordinate all NEXUS agents/modules around a single set of goals, policies, evidence rules and measurable outcomes.

## Why this exists

NEXUS has accumulated useful vertical capabilities, but the project evidence also shows duplicate registries/checkpoints, state drift, and cases where reported progress did not always correspond to a net-new capability. The control plane is therefore a governance and routing layer, not another cosmetic agent.

## Core loop

`SENSE -> RESOLVE -> VERIFY -> PRIORITIZE -> ROUTE -> EXECUTE -> TEST -> RECORD -> EVALUATE -> IMPROVE`

## Promotion loop

`Observation -> Outcome -> Evaluation -> Change Proposal -> Sandbox -> Regression Suite -> Policy/Human Gate -> Versioned Promotion -> Rollback`

## Minimum topology

1. Meta-Orchestrator / Control Plane
2. Research + Evidence Worker
3. Domain Reviewer selected by task (commercial or engineering)
4. Communication Worker, draft-only by default
5. QA/Evaluator + Policy Gate
6. Opportunity Scout, discovery-only until authorized

Most capabilities should remain tools/modules rather than autonomous agents.

## Canonical registries

Only one canonical instance of each logical registry should accept new operational writes:

- Goal Registry
- Agent Registry
- Work / Task Registry
- Evidence / Authority Registry
- Decision / Approval Registry
- Outcome / Evaluation Ledger
- Connector Health Registry
- Change / Experiment Registry

Duplicates become archive/read-only until migrated or deleted.

## Agent contract

Each agent must declare:

- stable agent id
- role
- version
- maturity: designed / implemented / tested / production
- capabilities
- authority set
- project scopes
- health: healthy / degraded / offline
- max parallel tasks
- measured quality/cost/latency inputs

No agent receives work outside its capabilities, scope, authority or health envelope.

## Non-negotiable invariants

- External/high-risk actions require the approval gateway and are not auto-routed.
- Supplier claims cannot overwrite buyer-confirmed engineering authority.
- Cross-project values must never propagate without explicit provenance and authorization.
- Duplicate outreach/action keys are blocked.
- Offline connectors/agents cannot be treated as healthy dependencies.
- `designed != implemented != tested != production` is machine-visible state.
- Agent self-improvement produces a change proposal, not automatic production mutation.
- Promotion requires regression tests, versioning, comparison to the prior baseline, and rollback capability.

## Improvement metrics

Primary quality metrics:

- duplicate outreach rate
- unsupported claim rate
- stale-authority error rate
- cross-project contamination rate
- task-loss rate
- false-completion rate
- human correction rate
- approval-policy violations
- connector recovery success
- opportunity usefulness / precision
- supplier qualification precision
- time-to-decision

## Rollout

### P0

- adopt canonical Agent + Goal + Work registries
- wire existing verticals through control-plane routing
- enforce project scope and dedupe keys
- require explicit external-action approval
- add health state for connectors/agents

### P1

- connect Outcome/Evaluation Ledger
- add versioned change proposals and regression promotion
- reconcile/archive duplicate Notion registries
- add state-drift detector between database / Notion / GitHub / chat summaries

### P2

- event log / PostgreSQL-backed runtime state
- calibrated routing from historical outcomes
- scheduled discovery and opportunity portfolio management
- multi-model reviewer routing only when measured advantage exists

## Definition of progress

Progress is accepted only when at least one of these changes measurably: capability, test coverage, reliability, business outcome, decision quality, cycle time, or risk reduction. Repeated status narration is not progress.
