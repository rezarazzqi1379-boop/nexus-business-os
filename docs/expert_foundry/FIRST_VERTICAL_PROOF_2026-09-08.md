# Expert Foundry — First Vertical Proof

Date: 2026-09-08  
Project: `steel_ingot_pilot`  
State: `READY_FOR_FACTORY_DATA`  
Execution boundary: retrospective/read-only; no recipe, setpoint, equipment control or outreach.

## Direct result

The executable proof successfully captured two scientific sources, the exact research
queries, current evidence gaps, a falsifiable hypothesis, a hash-chained event log and a
digest-bound snapshot. It correctly refused to produce a plant recommendation because
the factory input contract is incomplete.

The first useful plant study should compare one acceptable heat and one defective heat of
the same grade and route. It should reconstruct their timelines, validate measurement
quality, preserve operator observations separately from measurements, and produce ranked
hypotheses plus a measurement plan. It must not copy numerical setpoints from literature.

## Required factory evidence

- Product form (ingot/billet/bloom/slab), grade and customer acceptance standard.
- Furnace/caster route, capacity, equipment identifiers and relevant manufacturer limits.
- Target and measured chemistry, sampling time/location/method and laboratory method.
- Charge, alloy, deoxidizer, slag and refractory records with mass and time.
- Temperature/superheat timeline; treatment, vacuum and stirring records where applicable.
- Mould geometry, casting speed, mould level and cooling-zone measurements.
- Heat IDs, historian/LIMS extracts, maintenance deviations and operator observations.
- Defect taxonomy, sample locations, macroetch/inclusion/chemistry and mechanical results.

## Scientific evidence ledger

- ISO 14284:2022 — sampling and preparation for chemical-composition determination in
  iron and steel. Scope verified; procedure is paywalled.
  https://www.iso.org/standard/77332.html
- ASTM E415-21 — Spark-OES for carbon and low-alloy steel within specified analytical
  ranges; requires suitable specimens and reference materials.
  https://store.astm.org/e0415-21.html
- ASTM E381-22 — macroetch examination of billets and blooms can expose segregation,
  cracks, porosity and pipe; sampling/rating must be agreed and chemical safety controlled.
  https://store.astm.org/e0381-22.html
- ISO 4967:2026 — micrographic inclusion determination for rolled/forged products; not a
  direct as-cast acceptance method. https://www.iso.org/standard/86687.html
- Li et al., 2024 — macrosegregation and shrinkage porosity are coupled to composition,
  ingot size, flow and solidification conditions. https://doi.org/10.1016/j.pnsc.2024.05.009
- Lesoult, 2005 — macrosegregation is difficult to remove downstream and quantitative
  prediction remains process-specific. https://doi.org/10.1016/j.msea.2005.08.203
- Wang et al., 2020 — plant trials in a scoped stainless grade show calcium-treatment
  effects can be non-linear; its numerical range must not be transferred to another grade.
  https://doi.org/10.1016/j.jmrt.2020.08.017
- NIST/SEMATECH Engineering Statistics Handbook — measurement characterization and DOE
  principles for defensible experiments. https://www.nist.gov/programs-projects/nistsematech-engineering-statistics-handbook

## Experience-to-evidence protocol

Operator experience remains an observation until it passes this chain:

`incident → raw account/log → context and units → conditional claim → falsifiable
hypothesis → measurement-system check → safe approved experiment → independent
replication → human promotion decision`

The capture interview should reconstruct an actual event and preserve cues, decisions,
rejected alternatives, anomalies and outcomes. It should include at least two people from
different shifts where practical. Raw material must remain distinct from interpretation;
contradictions and neutral/failed results are retained.

Method anchors: Critical Decision Method (https://doi.org/10.1109/21.31053), NIST DOE
(https://www.itl.nist.gov/div898/handbook/pmd/section3/pmd31.htm), UK HSE shift handover
(https://www.hse.gov.uk/humanfactors/topics/shift-handover.htm), and OSHA incident
investigation (https://www.osha.gov/incident-investigation).

## Acceptance gate for the next run

Use one good and one defective historical heat of the same grade/route. The run passes
only if every conclusion links to raw evidence, units and uncertainty are explicit,
contradictions remain visible, and the output stops at hypotheses and a measurement plan.
Any live trial requires separate engineering, operations and HSE approval with documented
limits, stop conditions and rollback.
