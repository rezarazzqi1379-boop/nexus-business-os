# Claude Focused Handoff — Billet-to-Strip Rolling Study

Prepared: 2026-09-14  
Project ID: `rolling_mill_strip_300_pilot`  
Current state: `READY_FOR_ENGINEER_INTERVIEW`  
Decision boundary: retrospective engineering study only; no operating change authorized.

## User objective

Help determine whether and how the existing rolling line could produce the intended
"300" strip product from the existing "150" billet, using current machinery if feasible.
The system must combine literature, machine constraints, historical production data and
operator experience, but must not invent machine meanings, units or production settings.

## Raw user statement

The following is voice-transcribed conversation evidence and remains `UNVERIFIED`:

> دستگاه نورد یا رافینگ. توانایی تولید شمش ۱۵۰. از شمش ۱۵۰ تسمه ۲۵۰ می‌گیرند.
> غلطکه ۴۵۰ تا ۴۸۰. طول ۱۳۵۰. گیربکس ۱ به ۱۰. همدور ۵۵۰. موتور ۸۰۰
> ۱۲۵ کیلووات ۱۰۰۲. رافینگ: استند ۳ غلطکه، ۲ غلطکه، فینیش ۲ غلطکه.
> تولید، ضخامت از ۶ تا ۲۰. عرض ۱۵، ۲۰، ۲۵. ... چجوری از طریق اینها تسمه
> ۳۰۰ گرمی بگیریم و عرض...

Do not silently normalize these numbers. In particular:

- `150` may be a 150×150 mm billet, but that is not verified.
- `250` may be strip width in mm, but that is not verified.
- `300` may be target width, mass per length, or another quantity.
- `450–480` may be working roll diameter, new-to-worn diameter, or another dimension.
- `1350` may be roll barrel length or another length.
- `550` may be motor/input/output/roll RPM or something else.
- `800`, `125 kW`, and `1002` may be separate nameplate fields; only 125 kW has an
  apparent unit, and none is verified from a photo.
- `15/20/25` may mean 150/200/250 mm widths or literal 15/20/25 mm values.

## What the repository already provides

- Structured unresolved claims and machine-data contract:
  `.nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json`
- Fail-closed readiness assessment: `rolling_mill_intake.py`
- Engineer interview: `docs/expert_foundry/ROLLING_MILL_ENGINEER_QUESTIONNAIRE_FA.md`
- Project audit: `docs/expert_foundry/ROLLING_MILL_PROJECT_AUDIT_2026-09-12.md`
- Governed memory and ingestion: `expert_foundry.py`, `foundry_ingestion.py`
- Tests: `evals/test_rolling_mill_intake.py` plus Expert Foundry ingestion tests.

Current gate output blocks calculation and operation change until required values are
typed, positive where applicable, and bound to evidence. Safety flags require literal
`true`, not a string or placeholder.

## Claude's continuing role

Claude should own the scientific/mechanical review of this focused topic while preserving
the repository's evidence discipline:

1. Convert every new answer/photo/drawing into FACT, MEASUREMENT, CLAIM or UNKNOWN.
2. Maintain a question-to-evidence ledger and never overwrite raw inputs.
3. Identify the meaning and unit of every current number before calculation.
4. Ask for the smallest missing evidence batch, starting with motor/gearbox nameplates,
   roll/groove drawing, and a successful historical 250 pass table.
5. Once the intake gate passes, calculate only a retrospective feasibility envelope:
   area/volume consistency, speed ratio, roll bite, reduction, spread, force, torque,
   power and equipment utilization—with assumptions, uncertainty and model applicability.
6. Independently compare calculations with measured current/RPM/temperature data.
7. Generate alternative hypotheses and disconfirming tests.
8. Stop before any live pass schedule, roll gap, speed or trial recommendation unless an
   engineer validates equipment limits and the user gives exact approval for a bounded trial.

## Mandatory first response

After inspecting actual files, Claude should return:

- verified archive/file hashes;
- exact current status and missing fields;
- a short Persian questionnaire containing only the next 8–12 highest-value questions;
- a list of photos/files needed from the engineer;
- any P0/P1 flaw found in the intake model;
- what can be calculated now versus what is blocked;
- no recipe, setpoint or trial instruction.

## Technical evidence anchors

- Said et al., temperature, roll force and torque in hot bar rolling:
  https://doi.org/10.1016/S0924-0136(98)00391-4
- Sims, calculation of roll force and torque in hot rolling mills:
  https://doi.org/10.1243/PIME_PROC_1954_168_023_02
- Wang et al., data-driven roll force/torque model and parameter families:
  https://doi.org/10.2355/isijinternational.ISIJINT-2018-846
- OSHA machine guarding and in-running nip hazards:
  https://www.osha.gov/etools/machine-guarding/introduction/general-requirements

These sources identify relevant variable families; their numerical values are not plant
setpoints and cannot be transferred without plant-specific validation.
