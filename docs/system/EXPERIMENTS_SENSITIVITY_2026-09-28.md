# Slab-Line What-If Sensitivity Report

Generated 2026-09-28. **This is sensitivity analysis on a concept model (`slab_line_design.py`) — not a set of operating setpoints, recipes, or trial instructions.** Every row below perturbs one UNSOURCED or literature-range engineering assumption (see `docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md`) and recomputes the model; nothing here has been released, purchased, or sent to a vendor.

## 1. `friction-mu` — MU — friction coefficient used for the bite limit and the 'balanced' schedule (slab_line_design.py:45, SCENARIOS['balanced']['mu'])

Values tested: 0.2, 0.25, 0.3, 0.35, 0.4

Basis: 0.25-0.35 is the literature range for hot flat rolling (Roberts/Ekelund, per MODEL_LITERATURE_VALIDATION item 1); 0.20 and 0.40 are edge cases outside that range. Nominal 'balanced' value is 0.30.

Reference: docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 1; slab_line_design.py:45-50

| value | peak F (MN) | peak roll T (kN·m) | peak P (kW) | gearbox out req (kN·m) | regen (kW) | accel/brake lo (/h) | accel/brake hi (/h) | capacity lo (t/h) | capacity hi (t/h) | finish@12mm (C) | finish@6mm (C) | bite limit (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.2 | 4.9 | 180 | 1.8e+03 | 264 | 675 | 306 | 510 | 17.3 | 35.7 | 841 | 629 | 12 |
| 0.25 | 4.95 | 199 | 1.99e+03 | 310 | 675 | 238 | 408 | 20.2 | 42.2 | 891 | 670 | 18.8 |
| 0.3 | 5.12 | 218 | 1.83e+03 | 341 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 0.35 | 5.29 | 239 | 1.87e+03 | 374 | 675 | 170 | 374 | 20.4 | 53.4 | 879 | 649 | 36.7 |
| 0.4 | 5.56 | 244 | 1.92e+03 | 382 | 675 | 170 | 374 | 20.4 | 53.4 | 879 | 649 | 48 |

## 2. `flow-stress-scale` — Flow-stress anchor scale factor on FS_A (slab_line_design.py:70, the sigma=A*exp(-beta*T)*... anchor)

Values tested: 0.85, 1, 1.15

Basis: the flow-stress anchor numbers (65/88/120/163 MPa at 1200-900 C) are UNSOURCED for their exact values (item 14): the literature check could not independently confirm them against a published Shida/Misaka table point. +-15% brackets that unresolved uncertainty; the model's own sensitivity note already shows this scales force/torque/power exactly 1:1.

Reference: docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 14 and section 2; slab_line_design.py:67-70

| value | peak F (MN) | peak roll T (kN·m) | peak P (kW) | gearbox out req (kN·m) | regen (kW) | accel/brake lo (/h) | accel/brake hi (/h) | capacity lo (t/h) | capacity hi (t/h) | finish@12mm (C) | finish@6mm (C) | bite limit (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 0.85 | 4.35 | 186 | 1.56e+03 | 290 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 1 | 5.12 | 218 | 1.83e+03 | 341 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 1.15 | 5.89 | 251 | 2.11e+03 | 392 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |

## 3. `grade` — Steel grade flow-stress multiplier (slab_line_design.py:72-78, GRADES)

Values tested: S235JR, S355JR

Basis: S355JR carries a +15% flow-stress multiplier over S235JR from an UNSOURCED '~6%/%Mn rule of thumb' (item 15). The vendor RFIs are all computed at S355JR (the declared hard case); the transmission fragility check for this experiment tests what happens if the true multiplier is actually the S235JR one (i.e. the +15% rule is wrong), against those S355JR-basis RFI numbers.

Reference: docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 15; slab_line_design.py:72-78

| value | peak F (MN) | peak roll T (kN·m) | peak P (kW) | gearbox out req (kN·m) | regen (kW) | accel/brake lo (/h) | accel/brake hi (/h) | capacity lo (t/h) | capacity hi (t/h) | finish@12mm (C) | finish@6mm (C) | bite limit (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S235JR | 4.45 | 190 | 1.6e+03 | 296 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| S355JR | 5.12 | 218 | 1.83e+03 | 341 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |

## 4. `rotor-inertia` — motor_rotor_j — rotor (+ drive-train) inertia referred to the motor shaft, kg*m^2 (slab_line_design.py inertia_at_motor_kgm2 / motor_duty / braking_per_stop argument)

Values tested: 250, 450, 750

Basis: Package A's plausible range for a ~1600 kW / 350 rpm DC mill motor; item 28, UNSOURCED — no manufacturer nameplate or handbook figure was retrieved. Governs regen power and reversal commutation utilisation, not any rolling-force/torque/power number.

Reference: docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 28; slab_line_design.py inertia_at_motor_kgm2()

| value | peak F (MN) | peak roll T (kN·m) | peak P (kW) | gearbox out req (kN·m) | regen (kW) | accel/brake lo (/h) | accel/brake hi (/h) | capacity lo (t/h) | capacity hi (t/h) | finish@12mm (C) | finish@6mm (C) | bite limit (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 250 | 5.12 | 218 | 1.83e+03 | 341 | 254 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 450 | 5.12 | 218 | 1.83e+03 | 341 | 422 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 750 | 5.12 | 218 | 1.83e+03 | 341 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |

## 5. `ramp-time` — Accel/brake ramp time, s (slab_line_design.py motor_duty accel_time_s / braking_per_stop decel_s argument)

Values tested: 2, 3, 4

Basis: the RFIs bracket 2-3 s for the accel-torque figure and state 3 s for the regen-power figure; no single literature citation pins the ramp time — it is a drive-train design choice, tested here alongside the 2-4 s bracket the vendor documents already span.

Reference: nexus_checks/transmission.py compute_accel_torque_range / compute_regen_680 (2-3 s basis)

| value | peak F (MN) | peak roll T (kN·m) | peak P (kW) | gearbox out req (kN·m) | regen (kW) | accel/brake lo (/h) | accel/brake hi (/h) | capacity lo (t/h) | capacity hi (t/h) | finish@12mm (C) | finish@6mm (C) | bite limit (mm) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 5.12 | 218 | 1.83e+03 | 341 | 1.01e+03 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 3 | 5.12 | 218 | 1.83e+03 | 341 | 675 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |
| 4 | 5.12 | 218 | 1.83e+03 | 341 | 506 | 204 | 374 | 21 | 46.6 | 898 | 673 | 27 |

## 6. `ar3-threshold` — Ar3 (austenite->ferrite) threshold, C — thermal pass/fail cutoff. NOT a slab_line_design.py constant: Ar3 is computed nowhere in the model, only compared against here.

Values tested: 630, 750, 820, 850

Basis: two literature sources disagree by ~200 C (item 30): 820-850 C is the commonly cited generic C-Mn/TMCP hot-rolling range; ~630 C comes from a published regression fitted to a DIFFERENT (Nb-microalloyed pipeline) steel family, extrapolated outside its fitted domain. Neither is chemistry-matched to this project's S235JR/S355JR heats. 750 C is an interpolated midpoint scenario, not a third literature source.

Reference: docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 30 and section 2 (Ar3 disagreement note)

| Ar3 threshold (C) | 6 mm | 8 mm | 10 mm | 12 mm | 15 mm | 20 mm | 25 mm | 30 mm | thicknesses passing |
|---|---|---|---|---|---|---|---|---|---|
| 630 | 673 C PASS | 789 C PASS | 810 C PASS | 898 C PASS | 975 C PASS | 1041 C PASS | 1091 C PASS | 1095 C PASS | 8/8 |
| 750 | 673 C FAIL | 789 C PASS | 810 C PASS | 898 C PASS | 975 C PASS | 1041 C PASS | 1091 C PASS | 1095 C PASS | 7/8 |
| 820 | 673 C FAIL | 789 C FAIL | 810 C FAIL | 898 C PASS | 975 C PASS | 1041 C PASS | 1091 C PASS | 1095 C PASS | 5/8 |
| 850 | 673 C FAIL | 789 C FAIL | 810 C FAIL | 898 C PASS | 975 C PASS | 1041 C PASS | 1091 C PASS | 1095 C PASS | 5/8 |

## Fragility matrix — nexus_checks.transmission claims vs. experiments

`stable`: rounded vendor-facing number unchanged. `moves`: rounded value changes by less than 25%. `breaks`: rounded value changes by 25% or more, or recomputation fails outright. `CLAIMS_INPUT` entries (no model function behind them) are not shown - there is nothing to recompute for them.

Note on `accel-torque-12-29`: its reported 12-29 kN·m bracket already mixes two different (rotor inertia, ramp time) pairs - 450 kg·m² @ 3 s for the low end, 750 kg·m² @ 2 s for the high end. A single swept `rotor-inertia` or `ramp-time` value can match at most one end of that bracket, never both, so this claim shows `breaks` at every tested value of those two experiments by construction - that is a property of the claim's own basis, not a sign that the model itself is unstable.

| claim | friction-mu | flow-stress-scale | grade | rotor-inertia | ramp-time | ar3-threshold |
|---|---|---|---|---|---|---|
| accel-brake-204-374 | breaks | stable | stable | stable | stable | stable |
| reversals-85-170 | breaks | stable | stable | stable | stable | stable |
| gearbox-rated-345-420 | moves | moves | moves | stable | stable | stable |
| gearbox-guaranteed-peak-685 | moves | moves | moves | stable | stable | stable |
| gearbox-expansion-peak-840 | moves | moves | moves | stable | stable | stable |
| duty-bite-impact-455-682 | moves | moves | moves | stable | stable | stable |
| accel-torque-12-29 | stable | stable | stable | breaks | breaks | stable |
| regen-680-at-3s | stable | stable | stable | breaks | breaks | stable |
| stand-peak-force-5.12mn | moves | moves | moves | stable | stable | stable |
| stand-peak-torque-218.3 | moves | moves | moves | stable | stable | stable |
| stand-spindle-torque-120.1 | moves | moves | moves | stable | stable | stable |
| ratio-7.1 | stable | stable | stable | stable | stable | stable |
| pinion-centre-646mm | stable | stable | stable | stable | stable | stable |
| gearbox-service-factor-2.21 | stable | stable | stable | stable | stable | stable |

## Ranked: inputs that most move vendor-facing numbers

1. `friction-mu` — 2 claim(s) BREAK, 34 claim(s) MOVE across its tested values
2. `flow-stress-scale` — 0 claim(s) BREAK, 14 claim(s) MOVE across its tested values
3. `rotor-inertia` — 5 claim(s) BREAK, 0 claim(s) MOVE across its tested values
4. `ramp-time` — 5 claim(s) BREAK, 0 claim(s) MOVE across its tested values
5. `grade` — 0 claim(s) BREAK, 7 claim(s) MOVE across its tested values
6. `ar3-threshold` — 0 claim(s) BREAK, 0 claim(s) MOVE across its tested values

