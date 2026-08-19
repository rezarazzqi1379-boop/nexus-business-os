# Decision Learning v0.1

## Why

NEXUS already records evidence, signals, opportunities and outcomes, but it also needs a disciplined way to compare a prior decision or prediction with what actually happened. Without that layer, hindsight can overwrite the original reasoning and uncalibrated scores can create false precision.

## Chain

`Decision -> Observation -> Evaluation -> Learning -> Next Action`

## Core rules

1. A decision must preserve its original rationale, expected outcome, success criterion, review date, assumptions, unknowns and retrievable evidence references.
2. An observation must point to retrievable evidence and retain its epistemic class: `fact | claim | estimate | inference | hypothesis | assumption | unknown`.
3. An evaluation cannot exist without an observation.
4. A decision marked `evaluated` must have both an observation and an evaluation.
5. Planned or active decisions cannot be silently rewritten as already evaluated.
6. v0.1 intentionally stores no numeric confidence score. NEXUS has not yet accumulated enough forecasts/outcomes to justify calibrated probability claims.
7. When real numeric metrics exist, store the metric in the evidence/outcome layer; do not convert qualitative judgment into a made-up percentage.

## Evaluation classes

- `confirmed` — the success criterion was met with adequate evidence.
- `partially_confirmed` — part of the expected outcome was supported, but important gaps remain.
- `disconfirmed` — the observed result contradicts the expected outcome or success criterion.
- `inconclusive` — evidence is insufficient or the review horizon has not produced a defensible conclusion.

## First shadow use

The Hydrotester/YAXING readiness decision is a suitable first case:

- Decision: hold final quotation until engineering-approved pipe length and wall-thickness/ID are known.
- Expected outcome: prevent provisional geometry from becoming final technical authority.
- Current status: active.
- Review: after engineering input or the next decision-relevant supplier reply.
- Evaluation should remain `inconclusive` until an actual outcome exists.

## Future calibration path

Only after a meaningful sample of predictions has both explicit prior expectations and later outcomes should NEXUS test probability calibration. At that point, candidate methods include reliability diagrams and Brier-style scoring for genuinely probabilistic forecasts. This is a future experiment, not a current scoring rule.

## Non-goals

- no automatic supplier scoring;
- no autonomous merge/deploy/send decisions;
- no replacement of the existing Outcome Ledger;
- no pseudo-precise confidence percentages;
- no historical rewriting of the original decision after the outcome is known.
