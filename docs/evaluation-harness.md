# NEXUS Evaluation Harness v0.1

## Objective

Create a deterministic, side-effect-free regression layer for structured NEXUS decisions before introducing more autonomous agent/tool behavior.

The harness evaluates **observations** against explicit **assertions**. It does not call models, tools, email, databases or external APIs.

## Design principles

- Evidence-backed cases only: every evaluation case requires at least one retrievable evidence reference.
- No arbitrary `eval`, expression execution or dynamic code.
- Dot-path lookup only across mapping/dictionary observations.
- Missing paths fail safely instead of throwing.
- Assertion IDs must be stable and unique within a case.
- Suite results report pass/fail counts; they are not calibrated business-confidence scores.
- The harness is independent of any single LLM or agent framework.

## Supported assertions

- `equals`
- `not_equals`
- `present`
- `absent`
- `contains`
- `not_contains`

## First regression example

Hydrotester requirement readiness can be represented as structured observations such as:

```python
{
    "decision": {
        "ready_for_discovery": True,
        "ready_for_final_quote": False,
    },
    "requirements": {
        "length_range": "unknown_blocking",
        "wall_thickness_or_id": "unknown_blocking",
        "max_pressure": "provisional",
    },
}
```

The evaluation then asserts that discovery remains open while final quotation is blocked and unknown buyer-side engineering inputs remain explicit.

## Intended future adapters

Only after the relevant features are independently accepted:

1. PR #1 adapter — verify supplier claims are not silently promoted to facts.
2. PR #2 adapter — verify `unknown_blocking` requirements prevent final quotation readiness.
3. PR #4 adapter — verify action-specific approval and capability-routing behavior.
4. Proposal ingestion adapter — compare extracted structured proposal fields against approved requirements and evidence provenance.
5. Agent-output adapter — validate structured agent results before any consequential tool/action gate.

## Non-goals

- no LLM-as-judge in v0.1;
- no autonomous external action;
- no production scoring model;
- no Supabase dependency;
- no telemetry vendor dependency;
- no attempt to prove commercial effectiveness from unit-test success.

## Promotion gate

Do not merge merely because unit tests pass. Review whether the harness catches a real regression in at least one active NEXUS feature branch before promoting it to the main runtime.
