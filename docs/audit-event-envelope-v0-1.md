# NEXUS Audit Event Envelope v0.1

Status: draft / shadow-mode infrastructure. No production exporter or external side effect.

## Problem being solved

NEXUS now has evidence semantics, requirement readiness, action-specific human gates, deterministic evaluation and promotion policy. The missing reliability layer is a stable way to correlate those control-plane decisions without copying sensitive supplier or commercial payloads into logs and without binding the canonical data model to one observability vendor.

This is an audit metadata envelope, not another agent, workflow engine, database or evaluation framework.

## Design

Each `AuditEvent` records only stable metadata:

- `event_id` — stable event identity;
- `trace_id` — groups one end-to-end control flow;
- `event_type` — evidence / decision / evaluation / promotion / human gate / action attempt;
- timezone-aware `occurred_at`;
- `actor_type`;
- `subject_ref` — a retrievable or stable object reference, not the object payload;
- `result_class` — observed / accepted / blocked / failed / passed / unknown;
- optional `parent_event_id` for causal nesting;
- optional `action_ref`, required for human-gate and action-attempt events;
- `evidence_refs` and `correlation_refs`;
- small non-sensitive tags;
- explicit privacy mode (`metadata_only` or `sensitive_omitted`).

v0.1 deliberately has **no free-form payload field**. Email bodies, prompts, LLM/tool inputs and outputs, prices, contracts, credentials and other sensitive content stay in their authoritative source systems and are referenced rather than copied.

## Validation / fail-closed rules

`validate_audit_trace(...)` rejects:

- empty event sets;
- invalid/missing stable IDs and subject refs;
- malformed or timezone-naive timestamps;
- unsupported event/actor/result/privacy values;
- duplicate event IDs;
- duplicate/blank evidence, correlation or tag values;
- human-gate/action-attempt events without an exact `action_ref`;
- missing parent events;
- parent links that cross trace IDs;
- parent cycles.

## First shadow chain

The regression fixture models the current Hydrotester control path:

`Gmail evidence → decision → deterministic eval → promotion decision → human action gate`

The event metadata links to the existing Gmail evidence and GitHub eval work while keeping commercial message content out of the audit envelope.

## External standards / portability

Primary-source research checked 2026-08-19:

- OpenAI Agents SDK tracing models an end-to-end workflow as a trace with unique trace IDs and child spans with parent IDs, timestamps and metadata. It also exposes controls for sensitive trace data.
- OpenTelemetry traces model spans with identity, parentage, attributes, events and links. Semantic conventions provide common naming, but convention areas can have different stability levels; GenAI conventions are still evolving/moving.

NEXUS therefore keeps this internal envelope canonical and may later add exporters/adapters. Export mapping must not change the internal meaning of event identity, evidence references, action scope or privacy mode.

References:
- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-python/running_agents/
- https://opentelemetry.io/docs/specs/otel/trace/api/
- https://opentelemetry.io/docs/specs/semconv/

## Non-goals

- no OpenAI tracing dependency;
- no OpenTelemetry SDK dependency;
- no model/tool payload capture;
- no Supabase writes;
- no production logging pipeline;
- no distributed workflow runtime;
- no new dashboard;
- no claim that software auditability proves commercial effectiveness.

## Promotion gate

Keep this branch Draft. Before integration, use it in shadow mode on the existing PR #9 control chain and verify that audit metadata can reconstruct control decisions without sensitive payload duplication. Independent review remains required before merge.
