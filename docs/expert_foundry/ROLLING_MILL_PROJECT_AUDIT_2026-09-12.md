# Rolling Mill Project Audit — 2026-09-12

## Direct assessment

The NEXUS repository has a governed evidence store, truthful static/live provenance modes,
raw-file vaulting, CSV/JSON/XLSX ingestion, project isolation, dry-run and human-gated
promotion. It did not have a rolling-mill-specific engineering contract. Therefore the
system could store files but could not determine whether the evidence was sufficient for
a width-expansion/pass-design study.

This increment adds that missing readiness gate. It deliberately performs no roll-force,
torque, bite, spread, motor-load or pass-schedule calculation until every consequential
machine claim has a unit, meaning and evidence locator.

## Current user evidence

The voice-transcribed equipment description is stored as eight `UNVERIFIED` claims. No
units or engineering meanings were inferred. In particular, `300` may mean width or mass;
`550`, `800`, and `1002` are not assigned to speed, voltage, current or model fields.

## What now becomes measurable

`rolling_mill_intake.py` reports one of two states:

- `READY_FOR_ENGINEER_INTERVIEW`: evidence or claim resolution is incomplete.
- `READY_FOR_RETROSPECTIVE_CALCULATION`: the data contract is complete enough to begin
  calculations on historical runs; this never authorizes a production change.

The final operation gate remains closed in both states. Any later trial needs independent
engineering review, documented equipment limits, hazard review and plant authorization.

## Remaining system gaps

- No calibrated rolling-force/torque/spread model exists yet.
- No pass-by-pass historical dataset has been supplied.
- No equipment drawing/nameplate/limit has been verified.
- No central multi-user UI or production deployment exists.
- Restore testing and externally signed ledger checkpoints remain incomplete.
- The repository-wide authority conflict for unrelated NEXUS/FAL documents remains open.
