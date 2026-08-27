# NEXUS Evaluation & Observability Watchlist — 2026-08-28

Status: RESEARCH INPUT / NO AUTHORITY.

## Problem-first objective
Create a vendor-neutral evaluation and observability layer so models, agents, routers, memory systems and workflow engines can be replaced without losing NEXUS acceptance history, provenance or outcome evidence.

## Current primary-source findings

### OpenAI Agents SDK tracing
- Built-in traces/spans cover workflow, agent, turn, generation, tool, guardrail and handoff events.
- Custom trace processors can export to other destinations.
- Sensitive-data handling and tracing availability must be checked for the intended data policy.
- NEXUS use: candidate trace adapter only; NEXUS event IDs, project IDs, authority/source refs and approval state remain canonical fields.

### OpenTelemetry semantic conventions
- Provides cross-platform naming conventions for traces, metrics, logs and events.
- Convention status can evolve, so NEXUS must own its stable event envelope and map to OTel rather than copy OTel fields into authority records.
- NEXUS use: interoperability/export vocabulary, not project/business authority.

## Required NEXUS trace envelope before external observability adoption
- event_id / trace_id / parent_id
- project_id and workspace_id
- task_id / action_id / experiment_id
- source_ref(s), source version(s), provenance hash
- epistemic class and authority tier
- model/provider/runner/tool adapter IDs
- input/output data classification
- approval class and exact approval binding when applicable
- timestamps and duration
- token/cost/latency measurements where available
- policy/security/contamination findings
- test/eval case IDs and verdicts
- rollback reference
- outcome / human corrections / business value when measurable

## Admission rule
No external eval/observability platform becomes a NEXUS dependency merely because it has richer dashboards. It must either reduce correction time, improve failure detection, improve reproducibility, or lower integration cost while preserving portable event export and project isolation.

## Next candidates to research when justified
- OpenAI Agents SDK tracing processors
- OpenTelemetry exporters/collectors and GenAI semantic conventions
- Phoenix / LangSmith / other eval-observability systems only through a frozen benchmark and data-retention review

No credentials, telemetry export, hosted trace ingestion or production instrumentation is authorized by this research note.
