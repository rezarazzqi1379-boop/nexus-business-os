# NEXUS Evaluation Harness v0.1

## Objective

Create one deterministic, side-effect-free regression layer for structured NEXUS decisions before introducing more autonomous agent/tool behavior.

The harness evaluates **observations** against explicit **assertions**. It does not call models, tools, email, databases or external APIs.

## Design principles

- Evidence-backed cases only: every evaluation case requires at least one retrievable evidence reference.
- No arbitrary `eval`, expression execution or dynamic code.
- Dot-path lookup only across mapping/dictionary observations.
- Missing paths fail safely instead of throwing.
- Assertion IDs must be stable and unique within a case.
- Suite results report pass/fail counts; they are not calibrated business-confidence scores.
- The harness is independent of any single LLM or agent framework.
- There is one canonical evaluation core. Promotion policy consumes its results rather than defining a second case/result engine.

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

## Regression core vs promotion policy

`nexus_evals.harness` owns deterministic evaluation semantics: cases, assertions, validation and suite results.

`nexus_evals.promotion` is a separate policy layer over those already-evaluated results. It records exact run/config versions, case-level observed counters, critical case IDs and explicit blockers. It does **not** re-evaluate observations or define a parallel `EvalCase` / `EvalCaseResult` model.

Promotion can be blocked by explicit limits on:

- failed cases;
- unsupported claims;
- policy violations;
- any failed critical case when zero critical failures are required.

The policy uses counts rather than an opaque aggregate intelligence score or a pseudo-calibrated business score. Invalid run/policy inputs fail closed with `invalid_promotion_input`.

## Consolidation decision for draft PR #8

Draft PR #8 explored useful run metadata, critical cases and explicit promotion blockers, but it also introduced a second evaluation case/result model. The useful promotion concepts are consolidated here as a consumer of the canonical regression core. Until this consolidation is independently reviewed and CI-tested, PR #8 remains historical/draft evidence and should not be merged in parallel.

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

A passing CI run proves implementation/test integrity only. Promotion additionally requires a real regression replay, independent review, and a deliberate merge decision. No merge, deployment, send or other consequential external action is authorized by this harness.
