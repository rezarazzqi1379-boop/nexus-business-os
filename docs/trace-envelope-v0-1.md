# NEXUS Trace Envelope v0.1

## Purpose

Create one provider-portable, privacy-first audit envelope that can reconstruct a NEXUS execution chain without copying sensitive commercial/model/tool payloads into telemetry.

Canonical implementation: `nexus_observability.events`.

The common control chain is:

`Evidence → Decision → Evaluation → Promotion → Human Approval → External Action Request`

Tool/workflow/error events may also exist, but every parent link must remain explicit and reconstructable.

## Consolidation decision

An overlap audit found two candidate `TraceEvent` implementations on the same draft branch: one under `nexus_core.trace` and one under `nexus_observability.events`. Two trace contracts would recreate the dual-framework problem previously found in evaluation.

Decision: `nexus_observability` is canonical. The duplicate `nexus_core.trace` implementation was removed. Trace-level graph validation was consolidated into `nexus_observability.events`.

## Design principles

- stable `event_id` and `trace_id` values;
- exactly one trace root;
- explicit parent links with cycle detection;
- actor identity at the system/component level;
- event-specific references (`decision_ref`, `eval_ref`, `action_ref`);
- retrievable evidence references rather than copied evidence payloads;
- optional `payload_ref` only to an approved source-of-record;
- metadata attributes are allowlisted and compact;
- no provider-specific OpenTelemetry/OpenAI field names in the canonical schema;
- no automatic external action;
- fail closed on malformed, orphaned, cyclic, mixed-trace or privacy-unsafe events.

## Privacy rule

Commercial emails, contracts, pricing, credentials, supplier proposals, full model prompts/responses, tool payloads and attachment contents stay in their approved source-of-record.

The trace envelope stores metadata and references only. Free-form attribute keys are rejected, known sensitive key patterns are rejected, and multiline/large attribute strings are rejected to reduce accidental payload leakage.

This is a defense-in-depth boundary, not a proof that arbitrary metadata is non-sensitive. Callers must still avoid placing secrets or commercial content into metadata fields.

## Event types

- `workflow_started`
- `workflow_finished`
- `evidence_read`
- `decision_recorded`
- `evaluation_completed`
- `promotion_decided`
- `tool_requested`
- `tool_completed`
- `approval_requested`
- `approval_decided`
- `guardrail_triggered`
- `external_action_requested`
- `error`

## Validation invariants

1. Every event has nonblank stable IDs, timestamp string and actor.
2. All events in one validated graph share exactly one `trace_id`.
3. Event IDs are unique.
4. Parent references resolve inside the same trace graph.
5. Parent links cannot form cycles.
6. A trace graph has exactly one root.
7. `evidence_read` requires at least one evidence reference.
8. `decision_recorded` requires `decision_ref`.
9. `evaluation_completed` and `promotion_decided` require `eval_ref`.
10. Approval/external-action events require `action_ref`.
11. Arbitrary free-form trace attributes are not allowed.
12. Stable serialization uses internal NEXUS names, not vendor telemetry names.

## Relationship to current draft PRs

- PR #1 supplies explicit evidence semantics.
- PR #2 supplies requirement-readiness decisions.
- PR #4 supplies action-scoped human gates.
- PR #6 supplies deterministic evaluation and promotion results.
- PR #7 supplies decision/outcome records.

This branch is stacked on PR #6 only to reuse the current canonical evaluation foundation. It does not import unfinished feature branches. Cross-branch proof belongs in the integration shadow.

## Non-goals

- no telemetry backend;
- no OpenTelemetry exporter yet;
- no model/tool payload logging;
- no database schema;
- no Supabase writes;
- no distributed tracing runtime dependency;
- no autonomous action execution;
- no claim that tracing itself improves business outcomes.

## Promotion gate

Before this becomes canonical runtime infrastructure:

- full tests must pass;
- at least one real NEXUS workflow must be represented as a trace without sensitive payload copying;
- integration must bind real decision/eval/gate outputs to the trace envelope;
- independent review must check privacy boundaries, orphan/cycle handling and whether required references are sufficient for audit reconstruction.
