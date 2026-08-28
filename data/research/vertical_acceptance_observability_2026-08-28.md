# NEXUS Vertical Acceptance + Observability v0.1 — 2026-08-28

## Purpose
Upgrade the existing Evaluation Constitution from frozen-case correctness into measured real-vertical acceptance without adding another agent runtime, database, router, or authority layer.

## Canonical NEXUS requirement
Master Context v1.9 requires the next promotion to use live evidence and measurable vertical acceptance tests. It specifically calls for measuring correction rate, blocked unknowns, duplicate prevention and decision time before further automation.

## New infrastructure
`vertical_acceptance.py` adds a provider-neutral measurement contract for real vertical runs:
- human correction rate;
- unknown-block rate when unknowns are encountered;
- duplicate-prevention rate when duplicates are attempted;
- mean decision time;
- hard failure on policy violations, cross-project leakage, external effects during evaluation, duplicate run IDs or sensitive trace payload capture.

Passing the harness never grants merge, deploy, production, connector-write or external-action authority. It only permits the next governed adoption gate.

## Observability design
The portable `TraceEnvelope` carries only workflow name, project ID, candidate ID, run ID and data classification. Sensitive payload capture is rejected by default.

This intentionally maps to current external practice without depending on any provider:
- OpenAI Agents SDK uses end-to-end traces and spans and supports workflow names, group IDs and metadata; its tracing docs warn that generation/function spans may contain sensitive data and expose a configuration to disable sensitive-data capture.
- OpenAI Agents SDK testing utilities support deterministic provider-neutral in-memory tests without model or sandbox-provider calls.
- MCP integrations can surface tool-list and tool-call activity in tracing, but remote MCP servers must be trusted and use least-privilege credentials plus approval for sensitive operations.

Primary references reviewed 2026-08-28:
- https://openai.github.io/openai-agents-python/tracing/
- https://openai.github.io/openai-agents-python/testing/
- https://openai.github.io/openai-agents-python/mcp/

## Promotion experiment
First target: Hydrotester qualification replay using held evidence. Compare the current governed workflow against a candidate workflow on the same evidence snapshot. Record the four required operational metrics plus all blocked contradictions. Do not contact vendors or mutate external state during the experiment.

## Rollback
This addition is isolated and stateless. Removing the module, tests and this note returns the repository to the prior Evaluation Constitution with no migration or production effect.
