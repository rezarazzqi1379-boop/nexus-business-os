# NEXUS Trace Envelope v0.1

## Purpose

Create a small, provider-portable audit envelope that can reconstruct one NEXUS execution chain without copying sensitive commercial/model payloads into telemetry.

The canonical chain is intentionally generic:

`Evidence → Decision → Evaluation → Promotion → Human Gate → External Action Request`

Not every workflow must use every event type, but parent links must remain explicit and reconstructable.

## Design principles

- stable `event_id` and `trace_id` values;
- exactly one trace root;
- explicit parent links with cycle detection;
- event-specific references (`decision_ref`, `eval_ref`, `action_ref`);
- retrievable evidence references rather than copied evidence payloads;
- no provider-specific OpenTelemetry/OpenAI field names in the canonical internal schema;
- no automatic external action;
- fail closed on malformed, orphaned, cyclic, mixed-trace or sensitive-payload events.

## Privacy rule

The canonical trace envelope stores metadata and references only. `sensitive_payload_included=True` is invalid by design.

Commercial emails, contracts, pricing, credentials, supplier proposals, full model prompts/responses and tool payloads should remain in their approved source-of-record. A trace may store a `payload_ref` when reconstruction is necessary and access-controlled, but not the sensitive payload itself.

## Event types

- `evidence_observed`
- `decision_recorded`
- `evaluation_completed`
- `promotion_decided`
- `human_gate_evaluated`
- `external_action_requested`

## Validation invariants

1. Every event has nonblank stable IDs, timestamp string and subject reference.
2. Every event belongs to exactly one trace.
3. Event IDs are unique.
4. Parent references resolve inside the same trace.
5. Parent links cannot form cycles.
6. A trace has exactly one root.
7. Evidence events require evidence references.
8. Decision events require a decision reference.
9. Evaluation/promotion events require an eval reference.
10. Human-gate/external-action events require an action reference.
11. Sensitive payload inclusion is rejected.

## Relationship to current draft PRs

- PR #1 supplies explicit evidence semantics.
- PR #2 supplies requirement-readiness decisions.
- PR #4 supplies action-scoped human gates.
- PR #6 supplies deterministic evaluation and promotion results.
- PR #7 supplies decision/outcome records.

This branch is stacked on PR #6 only to reuse the current canonical evaluation foundation. It must not create imports from unfinished feature branches. Cross-branch integration belongs in the integration shadow.

## Non-goals

- no telemetry backend;
- no OpenTelemetry exporter yet;
- no model/tool payload logging;
- no database schema;
- no Supabase writes;
- no distributed tracing platform dependency;
- no autonomous action execution;
- no claim that tracing itself improves business outcomes.

## Promotion gate

Before this becomes canonical runtime infrastructure:

- full tests must pass;
- at least one real NEXUS workflow must be represented as a trace without sensitive payload copying;
- integration must prove the trace can bind real decision/eval/gate outputs;
- independent review must check privacy boundaries, orphan/cycle handling and whether required references are sufficient for audit reconstruction.
