# Claude Focused Handoff — Billet-to-Strip Rolling Study

Prepared: 2026-09-14  
Project ID: `rolling_mill_strip_300_pilot`  
Current state: `READY_FOR_ENGINEER_INTERVIEW`  
Decision boundary: retrospective engineering study only; no operating change authorized.

## User objective

Help determine whether the existing rolling line could feasibly roll a user-declared
220 x 220 x 3000 mm billet into 300, 400 or 600 mm-wide product at 8--20 mm thickness,
using current machinery if feasible.
The system must combine literature, machine constraints, historical production data and
operator experience, but must not invent machine meanings, units or production settings.

## Latest typed user statement

The following is conversation evidence confirmed by the user. It is `USER_CONFIRMED`,
not independently `VERIFIED` against drawings, nameplates or production records:

> بیلت ۲۲۰ × ۲۲۰ میلی‌متر و طول ۳ متر است. عرض‌های مورد بررسی ۳۰، ۴۰ و
> ۶۰ سانتی‌متر و ضخامت ۸ تا ۲۰ میلی‌متر است. استند رافینگ موجود سه‌غلتکه،
> «قطر دور» ۵۵۰ سانتی‌متر و طول بشکه ۱۳۵۰ سانتی‌متر است. گیربکس «۱۵ تن»
> با نسبت ۱ به ۱۰ توصیف شده است. گرید ST37 اعلام شده است. برای حالت سه‌غلتکه
> و گزینه دوغلتکه باید قطر و طول غلتک، گیربکس و موتور بررسی شود.

Interpretation boundary:

- Treat 220 x 220 x 3000 mm, widths 300/400/600 mm, thickness 8--20 mm,
  three-high roughing, reported "diameter around" 550 cm, barrel length 1350 cm,
  nominal ratio 10:1 and grade label ST37 as user-confirmed claims.
- The existing 150 x 150 production description remains partially ambiguous.
- "15 ton" is not a sufficient gearbox engineering rating; output torque, service
  factor, speed, thermal capacity and nameplate/drawing evidence remain unknown.
- The engineering referent of "diameter around" is unknown. The exact grade
  standard/certificate, motor data, usable roll face, roll necks,
  bearings, housing, groove geometry, temperatures, pass history and equipment limits
  remain unknown. Do not infer them.

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
   stand/roll/groove drawings, and one successful comparable historical pass table.
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
