# SUPERSEDED — DO NOT USE

**Effective 2026-09-21, by owner instruction.**

The owner replaced the project's entire input data set. Everything below is
retained as history and is **not** to be used in any calculation, quotation or
document from this date.

## What is superseded

All project data and calculations that assume:

- a 150 x 150 x 3150 mm **billet** feedstock
- target widths of 250 / 300 / 400 / 600 mm from that billet
- a roll barrel diameter of 500 / 518 / 520 / 550 mm
- a barrel length of 1280 / 1350 mm
- a three-high stand, or the ST1-ST4 four-stand layout
- an AC wound-rotor 1250 kW / 999 rpm / 420 V / 2300 A main drive
- a 1:9.8 gearbox ratio
- furnace-to-roughing 12 m and roughing-to-ST2 21 m
- the five-point declared temperature profile 1250/1200/1050/950/800

This includes, but is not limited to:
`STEEL_ROLLING_LINE_CONCEPT_PACKAGE_v0_1.md`,
`ENGINEER_REQUIREMENT_ANALYSIS_2026-09-21.md`,
`DRIVE_TRAIN_SIZING_STUDY_2026-09-21.md`,
`ENGINEER_LETTER_FINAL_2026-09-21.md` and its drafts,
`rolling_line_concept.py`, `drive_train_sizing.py`,
`thermal_and_route_model.py`, `caliber_spread_model.py`,
`width_measurement_physics.py`, `steel_action_gates.py`,
and the ACTIVE values in `ROLLING_MILL_ENGINEERING_INTAKE.json`.

## What replaces it

`SLAB_LINE_PRELIMINARY_DESIGN_2026-09-21.md` and `slab_line_design.py`, built
from the owner's 2026-09-21 data set only:

    slab 400 x 125 x 3000 mm, 1177.5 kg    furnace 20 t/h    slab exit 1250 C
    product 400 mm wide, 6-30 mm thick
    two-high stand, work roll D 600 mm, barrel 600 mm
    declared maximum line speed 3 m/s      DC main drive

`slab_line_design.py` imports nothing from the superseded modules and reuses no
number from them.

## Why this file exists rather than a deletion

The project's standing rule is that no previous value is ever silently
overwritten and no contradiction is ever deleted. A superseded data set is
still the record of what was believed and when. It is marked, not erased.

## What is NOT superseded

Findings about published standards are facts about those documents, not project
data, and survive:

- EN 10058:2018 caps at 200 mm nominal width
- EN 10029:2010 requires w >= 600 mm and excludes wide flats
- EN 10051 excludes product rolled (rather than slit) below 600 mm
- EN 10048:1996 covers width < 600 mm but its tolerance tables stop at 15 mm
- DIN 59200:2001-05 covers t >= 4 mm and 150 < b <= 1250 mm
- EN 10163-2 covers plate and wide flats, default class A subclass 1
- EN 10025-2 CEV limits and mechanical properties

The engineering FAILURE MEMORY (FM-001 to FM-005) also survives: those are
lessons about method, not data.
