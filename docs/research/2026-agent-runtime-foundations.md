# NEXUS Agent Runtime Foundations — 2026-08-19

Status: research note / architecture input, not production runtime.

## Purpose

Capture current primary-source findings that materially affect future NEXUS agent/runtime design. This document does **not** authorize adding a large agent fleet or another runtime dependency.

## Primary sources reviewed

- OpenAI Agents SDK: https://openai.github.io/openai-agents-python/
- OpenAI Agents SDK tracing: https://openai.github.io/openai-agents-python/tracing/
- OpenAI Agents SDK guardrails: https://openai.github.io/openai-agents-python/guardrails/
- Model Context Protocol authorization: https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization
- MCP 2026-07-28 specification release note: https://blog.modelcontextprotocol.io/posts/2026-07-28/
- OpenTelemetry semantic conventions: https://opentelemetry.io/docs/specs/semconv/
- OpenTelemetry GenAI observability: https://opentelemetry.io/blog/2026/genai-observability/
- Temporal documentation: https://docs.temporal.io/

## Verified facts from the primary sources

### OpenAI Agents SDK

The SDK intentionally exposes a small set of primitives: agents, tools/handoffs, guardrails, sessions, human-in-the-loop mechanisms and tracing/evaluation support. Tracing covers model generations, tool calls, handoffs, guardrails and custom events. Tool guardrails can run before and after function-tool calls; approval and guardrail ordering can be controlled.

**NEXUS implication:** do not design a large agent fleet as the default. Start with one manager/control plane plus narrowly scoped tools or handoffs. Treat approval gates and evaluation as first-class runtime behavior, not prompt text.

### Model Context Protocol

MCP separates tools, resources and prompts as different control surfaces. HTTP authorization is based on explicit resource targeting and OAuth-style authorization. The 2026-07-28 release further emphasizes stateless protocol behavior, authorization hardening, cacheable list results and formal extensions.

**NEXUS implication:** future NEXUS MCP contracts should be least-privilege and resource-scoped. Read-only evidence retrieval and write-capable commercial actions should never share a broad implicit permission boundary.

### OpenTelemetry

OpenTelemetry semantic conventions provide standardized names for telemetry. GenAI observability conventions can represent model calls, tools and token usage, but parts of the semantic-convention surface remain under active development.

**NEXUS implication:** keep an internal, stable NEXUS event envelope and map/export it to external telemetry. Do not make database schema depend directly on experimental semantic-convention names.

### Temporal

Temporal provides durable execution designed to resume workflows after crashes, network failures or infrastructure outages.

**NEXUS implication:** Temporal is a candidate only for future workflows whose business value requires durable multi-hour/day execution. It is **not** justified merely because NEXUS wants more automation. Current ChatGPT automations, GitHub state and explicit checkpoints remain simpler until a measured durability problem appears.

## Architecture decisions for the next build stage

1. **Evaluation before autonomy.** A deterministic evaluation/regression harness should exist before production agentic actions.
2. **Action-scoped approval.** Approval must be bound to an exact action, not a global boolean or conversational assumption.
3. **Portable tracing.** Internal traces should store stable IDs, event type, timestamps, parent correlation, evidence refs, tool/action refs, result class and privacy metadata. Export adapters may later map to OpenAI tracing or OpenTelemetry.
4. **Sensitive payloads off by default.** Commercial emails, contracts, pricing, credentials and model/tool payloads should not be copied into traces unless explicitly necessary and policy-allowed.
5. **No durability platform yet.** Temporal/n8n/other workflow runtimes remain candidates, not dependencies, until failure-recovery or scheduling complexity exceeds current mechanisms.
6. **MCP-ready, not MCP-fiction.** Define future contracts but never claim a custom NEXUS MCP server/app is connected before the platform/account path is verified.

## Hypotheses to test

- A deterministic evaluation harness will catch regression in action gating and fact/claim semantics before supplier-facing automation is introduced.
- A small manager + tools/handoffs architecture will be easier to evaluate and audit than a multi-agent mesh for the current procurement workload.
- An internal portable trace envelope will reduce migration cost if NEXUS later changes tracing/export vendors.

These are hypotheses until tested in NEXUS; they are not permanent rules solely because external frameworks support them.
