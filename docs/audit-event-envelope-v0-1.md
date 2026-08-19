# NEXUS Audit Event Envelope v0.1

Status: draft / shadow-mode infrastructure. No production exporter or external side effect.

## Problem being solved

NEXUS now has evidence semantics, requirement readiness, action-specific human gates, deterministic evaluation and promotion policy. The missing reliability layer is a stable way to correlate those control-plane decisions without copying sensitive supplier or commercial payloads into logs and without binding the canonical data model to one observability vendor.

This is an audit metadata envelope, not another agent, workflow engine, database or evaluation framework.

## Design

Each `AuditEvent` records only compact stable metadata:

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

All string metadata is intentionally bounded: leading/trailing whitespace, control characters (including CR/LF) and values over 256 characters fail validation. This prevents reference/tag fields from becoming a covert payload or log-injection channel.

## Validation / fail-closed rules

`validate_audit_trace(...)` rejects:

- empty event sets;
- invalid/missing stable IDs and subject refs;
- malformed or timezone-naive timestamps;
- unsupported event/actor/result/privacy values;
- duplicate event IDs;
- duplicate/blank evidence, correlation or tag values;
- oversized, control-character or whitespace-padded metadata values;
- human-gate/action-attempt events without an exact `action_ref`;
- missing parent events;
- parent links that cross trace IDs;
- parent cycles.

## First shadow chain

The regression fixture models the current Hydrotester control path:

`Gmail evidence → decision → deterministic eval → promotion decision → human action gate`

The event metadata links to the existing Gmail evidence and GitHub eval work while keeping commercial message content out of the audit envelope.

## External standards / security research

Primary-source/security guidance checked 2026-08-19:

- OWASP logging guidance says sensitive information such as access tokens, passwords, connection strings, commercially sensitive information and higher-classification data should normally not be recorded directly. It also recommends sanitizing event data to prevent log injection, explicitly including carriage return and line feed characters.
- W3C Trace Context privacy guidance states trace correlation fields must not carry personally identifiable or otherwise sensitive information. Its security guidance recommends checking trace-header length and content and avoiding proprietary/confidential information in propagated trace state.
- OpenTelemetry Baggage warns that propagated context can unintentionally reach third-party resources and has no built-in integrity guarantee. NEXUS therefore does not treat external trace/baggage metadata as trusted authorization or evidence.
- OpenAI Agents SDK tracing and OpenTelemetry provide useful exporter targets, but they are not canonical NEXUS state.

Security consequence for future exporters: export only an explicit allowlist of fields, never use trace/correlation metadata as an authorization signal, and remove or transform sensitive references before crossing a trust boundary.

References:
- https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- https://www.w3.org/TR/trace-context/
- https://github.com/w3c/trace-context/blob/main/spec/50-privacy.md
- https://github.com/w3c/trace-context/blob/main/spec/51-security.md
- https://opentelemetry.io/docs/concepts/signals/baggage/
- https://www.w3.org/TR/baggage/
- https://openai.github.io/openai-agents-python/tracing/
- https://opentelemetry.io/docs/specs/otel/trace/api/

## Trust-boundary rule

Audit metadata may correlate an internal source-of-record, but it does **not** grant permission to read that source, does not prove the source is trustworthy, and must not be propagated automatically outside the current trust boundary. External exporters/adapters must independently enforce destination policy, field allowlists and access controls.

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

Keep this branch Draft. Unit hardening and CI are required, then refresh the existing PR #9 shadow integration against the exact hardened contract. Independent security/architecture review remains required before merge.
