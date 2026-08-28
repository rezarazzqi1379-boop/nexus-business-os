# ADR-003: NEXUS Agent Supervisor

## Status

Accepted as an experimental, disabled-by-default capability. Merged by PR #80\non 2026-08-28; no live Herdr installation or production activation is implied.

## Decision

NEXUS owns semantic task completion. Herdr and future runners only provide
execution observations. A runner reporting `done` or `idle` moves a task to
`produced`, never directly to `accepted`.

Acceptance requires an exact project and packet binding, a non-empty artifact,
declared evidence, declared passing tests, budget compliance, and any required
human approval. Blocked or unknown runner states fail closed and never receive
an automated answer.

## Why this is stronger than runner-only orchestration

Herdr is useful for terminal multiplexing, agent visibility, and session
recovery. Those capabilities do not prove that an artifact belongs to the
correct project, cites the required evidence, passes domain checks, or was
authorized. The Supervisor adds those missing semantics while remaining
runner-agnostic; Herdr is one replaceable adapter.

## Vertical proof

The first deterministic fixture uses the Hydrotester project boundary. Tests
cover false completion, cross-project contamination, packet mismatch, missing
evidence, missing tests, approval bypass, duplicate observations, and budget
exhaustion. No live engineering value or production action is inferred.

## Non-goals

- installing or operating Herdr on a production host
- autonomous replies to blocked agents
- credential, billing, deployment, or merge authority
- claiming performance or reliability superiority before a live benchmark

## Admission rule

Promote only after clean-host reproduction and a controlled pilot comparing
task completion correctness, recovery time, operator interventions, and cost
against plain Herdr. Rollback is removal of the adapter/supervisor branch; the
existing NEXUS workflow remains unchanged.
