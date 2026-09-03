# NEXUS Vertical Acceptance + Observability v0.1 — 2026-08-29

## Purpose
Upgrade the existing Evaluation Constitution from frozen-case correctness into measured real-vertical acceptance without adding another agent runtime, database, router, or authority layer.

## Canonical NEXUS requirement
Master Context v1.9 requires the next promotion to use live evidence and measurable vertical acceptance tests. It specifically calls for measuring correction rate, blocked unknowns, duplicate prevention and decision time before further automation.

## Measurement contract
`vertical_acceptance.py` provides a provider-neutral contract for real vertical runs:
- human correction rate;
- unknown-block rate when unknowns are encountered;
- duplicate-prevention rate when duplicates are attempted;
- mean decision time;
- hard failure on policy violations, cross-project leakage, external effects during evaluation, duplicate run IDs or sensitive trace payload capture.

Passing the harness never grants merge, deploy, production, connector-write or external-action authority. It only permits the next governed adoption gate.

## Metric-integrity hardening — 2026-08-29
A review found two ways an apparently clean run could overstate evidence:
1. zero unknowns or zero duplicate attempts produced `None` metrics that did not block PASS even when policy required those controls;
2. decision time was mandatory, encouraging invented timing when a real trace did not contain a measured value.

The contract now preserves missing decision time as `None` and fails closed on incomplete timing coverage. A positive unknown-block or duplicate-prevention threshold also requires those controls to have been exercised; absence of the event is recorded as unmeasured rather than silently accepted.

This prevents three forms of metric gaming:
- a workflow cannot prove duplicate prevention without an observed duplicate attempt;
- a workflow cannot prove unknown blocking without an observed unknown;
- a workflow cannot hide an unmeasured/slow run behind the mean of only measured runs.

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

## First Hydrotester replay gate
Project: `PRJ-HYD-01`.

Canonical decision baseline remains `HOLD PO / CONTINUE QUALIFICATION`. The controlled Decision Pack states that neither current proposal is PO-ready; GH is a conditional technical lead and Marley a commercial benchmark. Fresh evidence after that pack changes the event state but not the purchase-order conclusion: GH supplied a signed response containing performance/tooling claims that still require contractual/structural closure; Marley confirmed approximately 3–4 minutes per pipe, which materially deviates from the controlling 60 pipes/hour basis; ANZ reported on 29 Aug 2026 that its OEM review is still in progress and expects its best quote early the following week.

The first live replay is **NOT YET SCOREABLE AS AN ACCEPTANCE PASS** because the historical work did not capture all four required operational measurements on a common run boundary. In particular, exact per-run decision time and a controlled duplicate-attempt challenge were not instrumented prospectively. Those values remain UNKNOWN; they must not be reconstructed from chat duration or invented after the fact.

Next proof must therefore be prospective: freeze one sanitized Hydrotester evidence snapshot, start the measurement clock, execute the governed comparison once, intentionally replay one duplicate action candidate, record every surfaced/blocking unknown and any human correction, then stop without external effects. Only those observed values may enter `VerticalRunObservation`.

## Rollback
This addition is isolated and stateless. Removing the module, tests and this note returns the repository to the prior Evaluation Constitution with no migration or production effect.
