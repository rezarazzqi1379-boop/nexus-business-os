# Engineering Discovery Experiments — 2026-08-19

Status: exploratory only. Nothing in this document authorizes merge, deployment, external sends, permission changes, or production adoption.

## EXP-ENG-001 — Property-based validation hardening

- Domain: coding / reliability
- Evidence class: strong external technical documentation + local hypothesis
- Hypothesis: property-based generation will find malformed or boundary inputs not covered by current hand-written NEXUS validation regressions.
- Mechanism: use Hypothesis-style generated values against compact metadata, enum/runtime validation, evidence refs, WorkItem validation, and action-scoped approval boundaries.
- Evidence refs:
  - https://hypothesis.readthedocs.io/en/latest/
  - https://hypothesis.readthedocs.io/en/latest/stateful.html
- Smallest reversible test: add property tests to one pure validator without changing production behavior.
- Success metric: discovers at least one previously untested failing input class OR demonstrates stable fail-closed behavior across generated cases with acceptable CI runtime.
- Failure metric: adds substantial CI/runtime/maintenance cost without new coverage or failure discovery.
- Promotion rule: Keep/Scale only after a focused pilot; otherwise Modify/Kill.

## EXP-ENG-002 — Stateful Autonomy/Goal transition testing

- Domain: coding / state integrity
- Evidence class: strong external technical documentation + local hypothesis
- Hypothesis: generated action sequences can expose invalid state transitions, stale approvals, duplicate evidence, or blocked-to-runnable drift that isolated unit tests miss.
- Mechanism: model primitive state transitions and invariants, then generate sequences rather than only values.
- Evidence refs:
  - https://hypothesis.readthedocs.io/en/latest/stateful.html
- Smallest reversible test: one state machine around a deterministic internal planner/state model; no connectors or external actions.
- Success metric: catches an invalid transition/sequence or materially increases invariant coverage without flaky behavior.
- Failure metric: no incremental coverage over ordinary property tests or unstable/non-deterministic CI.
- Promotion rule: do not generalize stateful testing until the pilot proves unique value.

## EXP-ENG-003 — Tool-boundary guardrail mapping

- Domain: agent architecture / security
- Evidence class: strong official documentation + architecture hypothesis
- Hypothesis: where NEXUS later uses custom function tools through an agent runtime, tool-level guardrails can provide a useful second validation boundary around each invocation, but must not replace the canonical Capability Runtime or human gate.
- Mechanism: map canonical ActionIntent/capability checks to a thin adapter before custom function-tool execution; retain NEXUS as source of truth.
- Evidence refs:
  - https://openai.github.io/openai-agents-python/guardrails/
  - https://openai.github.io/openai-agents-python/
- Important limitation: official docs state tool guardrails apply to custom function tools, not every hosted/built-in tool or handoff path.
- Smallest reversible test: architecture adapter/prototype only; no production agent adoption.
- Success metric: blocks a deliberately malformed/unauthorized custom tool invocation while preserving exact action-scoped approval semantics and avoiding a second authorization system.
- Failure metric: duplicates canonical gating, creates inconsistent policy ownership, or gives false coverage over unsupported tool paths.
- Promotion rule: No-Action unless a real agent-runtime integration need appears.

## EXP-ENG-004 — Privacy-preserving tracing adapter

- Domain: observability / debugging
- Evidence class: strong official documentation + local hypothesis
- Hypothesis: SDK tracing may improve debugging of future agentic flows if canonical NEXUS audit metadata remains provider-neutral and sensitive payload capture is disabled/minimized.
- Mechanism: export allowlisted correlation metadata from canonical AuditEvent rather than making SDK traces canonical state.
- Evidence refs:
  - https://openai.github.io/openai-agents-python/tracing/
  - https://openai.github.io/openai-agents-python/config/
- Smallest reversible test: local/synthetic trace with sensitive-data capture disabled; no commercial/customer data.
- Success metric: reconstructs a synthetic workflow while exposing no sensitive payload and preserving canonical event ownership in NEXUS.
- Failure metric: requires duplicating audit state, leaks inputs/outputs, or creates vendor lock-in without measured debugging value.
- Promotion rule: defer until PR #10 audit envelope and a concrete agent runtime need are independently reviewed.

## Current decision
Prioritize EXP-ENG-001 first because it can improve existing deterministic validators without introducing a new runtime or architecture. EXP-ENG-002 follows only if sequence-level invariants remain a measured gap. EXP-ENG-003/004 stay design experiments until an actual agent-runtime requirement exists.