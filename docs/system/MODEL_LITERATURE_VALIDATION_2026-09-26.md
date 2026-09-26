# Literature Validation of Physics Assumptions — `slab_line_design.py`

**Scope:** independent literature check of the physics constants and sub-models in
`slab_line_design.py` (branch `integ/2026-09-26`), cross-read against
`docs/expert_foundry/ENGINEERING_PACKAGE_A_TECHNICAL_2026-09-21.md`,
`docs/system/TRANSMISSION_AUDIT_STEEL_2026-09-26.md`, the existing
`PRIOR_ART_AND_BENCHMARK_REGISTER.md` and `ROLLING_MILL_ENGINEERING_REFERENCE_KNOWLEDGE.md`.

**This is a research memo only.** No operating setpoint, pass schedule, recipe, trial
or equipment change is proposed or implied anywhere below. Nothing here has been
contacted with anyone. Every source is labelled **FACT** (the cited source says this)
or **CLAIM** (a secondary/summarized statement I could not verify against the primary
text within the search budget). Repo code was read only; a throwaway copy was executed
locally (`/tmp/.../scratchpad/slab_line_design.py`, unmodified) purely to compute
sensitivities — nothing in the repository was changed.

---

## 1. Summary table

| # | Constant (file:line) | Model value | Literature range / value | Sources | Class | Effect on headline result |
|---|---|---|---|---|---|---|
| 1 | `MU` friction, `slab_line_design.py:45` | 0.25 / 0.30 / 0.35 | 0.20–0.45 for hot steel strip at 30–40% reduction (CLAIM, thesis reviewing Ekelund/Roberts data); 0.25–0.7 quoted for mild-steel bar (CLAIM, same thesis) | Shu.ac.uk thesis §Abstract, reviewing Roberts *Hot Rolling of Steel* & Ekelund; ASME *J. Tribology* 124(4):840 (title only reached, paywalled — CLAIM) | **CONSISTENT** — mid-range | see §2, +8.7% force from 0.25→0.35 (measured locally) |
| 2 | `LAMBDA_ARM` = 0.48, `:51` | 0.48 | Sims' lever-arm factor for hot flat rolling is commonly quoted ≈0.5, without a single fixed number in the primary 1954 paper (torque is integrated over the arc, not reduced to one constant) — CLAIM, abstract-level only | Sims (1954), *Proc. IMechE* 168:191 (abstract/citations only — full text not reached); ScienceDirect "Roll Torque" topic page (secondary, gives L/a regression, not the 0.5 figure) | **EDGE** — plausible, single indirect source, not independently corroborated within budget | linear on torque (stated in model already) |
| 3 | `MU_BEARING` = 0.004, `:52` | 0.004 | Hydrodynamic oil-film ("Morgoil"-type) neck bearings: no exact number found; general hydrodynamic-bearing friction is of order 0.001–0.01 under full film (CLAIM, generic tribology sources) | Danieli DanOil product page (marketing, not a design value); MITCalc plain-bearing reference (generic) | **UNSOURCED** — plausible order of magnitude, no primary number found | negligible (model shows ≤2% of rolling torque) |
| 4 | `E_STEEL_MPA` = 200 000 MPa, `:53` | 200 GPa | 200–210 GPa is the standard handbook value for steel | Standard mechanical-engineering handbooks (not separately re-verified — treated as textbook FACT) | **CONSISTENT** | barrel deflection only (already tiny, 0.09 mm) |
| 5 | `EMISSIVITY` = 0.80, `:54` | 0.75–0.85 range | Oxidised iron/mill scale 0.85–0.89; rough ingot iron 0.87–0.95 (FACT, Transmetra emissivity table, itself a secondary compilation) | Transmetra emissivity table (PDF) | **EDGE** — model's range sits at or slightly below the published band for scale; the qualitative direction (high emissivity, oxidised surface) is right | ±0.05 → ∓12 °C at pass exit (model's own figure); doesn't change the Ar3 pass/fail calls at 12 mm or below |
| 6 | `CP` = 700 J/kg·K, `:55` | 700 | Specific heat of austenite ~680–750 J/kg·K in the 800–1200 °C band (CLAIM, general thermophysical data, not separately re-derived) | Generic steel thermophysical property compilations | **CONSISTENT** | linear on cooling rate |
| 7 | `K_STEEL` = 28 W/m·K, `:56` | 28 | Thermal conductivity of steel ~25–30 W/m·K near 1100 °C (CLAIM, generic) | Generic steel property data | **CONSISTENT** | only enters `biot_number()`, not the pass schedule |
| 8 | `SIGMA_SB` = 5.670×10⁻⁸, `:57` | exact | CODATA value 5.670374×10⁻⁸ W/m²K⁴ | Physical constant — FACT | **CONSISTENT / FACT** | — |
| 9 | `H_CONV` = 15 W/m²K, `:59` | 15 | Forced convection in air, textbook range ~10–50 W/m²K | Generic heat-transfer textbook range | **CONSISTENT** | minor vs. radiation term at these temperatures |
| 10 | `NECK_DIAMETER_RATIO` = 0.55, `:61` | 0.5–0.6 stated range | Neck/barrel diameter ratio 0.5–0.6 is a commonly cited proportion for two-high roll design (CLAIM — not independently re-derived from a primary handbook within budget) | Model's own docstring citation; not independently corroborated | **UNSOURCED** (plausible, single source) | stress ∝ d⁻³: neck 300 mm vs 330 mm ≈ −33% stress swing (already noted in Package A) |
| 11 | `BEARING_OFFSET_MM` = 250, `:62` | 250 | Equipment-specific; no general literature value applies | — | **N/A / Hold Point** (model already flags this correctly) | linear on neck stress |
| 12 | `ROLL_CONTACT_CHILL_C` = 8 °C/contact, `:63` | 8 | Roll-chill loss of a few °C to ~15 °C per bite is commonly reported for hot strip/plate mills depending on contact time and roll temperature (CLAIM, no single quantitative source pinned in this pass) | — | **UNSOURCED** (plausible) | small vs. radiative loss at long interpass times |
| 13 | `YIELD_FRACTION` = 0.96, `:65` | 0.96 | Typical hot-mill scale + crop loss 3–6% is standard industry knowledge; no specific citation pinned | — | **UNSOURCED** (plausible) | linear on product length |
| 14 | Flow stress `FS_A,FS_BETA,FS_M,FS_N`, `:70`; anchors 1200→65, 1100→88, 1000→120, 900→163 MPa at 10 s⁻¹, ε=0.3 | Arrhenius-type power law, own fit | No two independent primary Shida/Misaka numeric tables were retrieved within budget; secondary sources confirm the *functional form* (`σ = A·exp(mT)·ε̇^m1·ε^m2`, Hensel–Spittel/Shida-type) and give one worked Shida value (124.7 MPa) under unstated conditions — CLAIM only, not a clean cross-check point | ScienceDirect "Roll Pressure" topic page (Shida example figure, conditions not given); `ROLLING_MILL_ENGINEERING_REFERENCE_KNOWLEDGE.md` (already in the repo, cites Misaka 1967, Shida 1969, Hensel–Spittel form) | **UNSOURCED for the exact anchor numbers** — functional form is CONSISTENT with the literature family, but I could not independently confirm 65/88/120/163 MPa against a published Shida/Misaka table point | This is the single most consequential unresolved item — ±15% flow stress gives **±15% force/torque/power** exactly (measured locally, see §2) |
| 15 | `GRADES["S355JR"]` multiplier = 1.15, `:74` | +15% vs S235JR | "~6%/%Mn rule of thumb" is the model's own stated basis; I found no independent literature source for that specific rule within budget. General hot-flow-stress differences between low-C and higher-Mn/C structural grades are a real, well-known effect but I could not pin a number | — | **UNSOURCED** | linear on all grade-dependent loads (S355 vs S235 is uniformly 1.15× per TRANSAUDIT) |
| 16 | Wusatowski spread, `w=10^(-1.269(b/h)(h/D)^0.556)`, `:168` | as coded | This is the classical Sedláček/Wusatowski-compiled empirical spread-exponent form; already correctly attributed in the repo's own `ROLLING_MILL_ENGINEERING_REFERENCE_KNOWLEDGE.md` and `PRIOR_ART_AND_BENCHMARK_REGISTER.md` (Wusatowski 1969; El-Kalay & Sparling 1968, *J. Iron Steel Inst.*; ISIJ calibre-rolling coefficients, Tetsu-to-Hagané 63(12):1819 and 72(14):1877) | Wusatowski, *Fundamentals of Rolling* (1969); El-Kalay & Sparling (1968) — both already cited in the repo registers, not duplicated here | **CONSISTENT** — recognised textbook form; the model's own docstring correctly states the ±10–20% scatter this family of formulas carries | see model's own note: negligible for this wide slab (b/h = 3.2→67) |
| 17 | `geometry_factor` Q_p (friction-hill), `:196` | `0.8+0.2·L/h` (L/h<1); `1+μL/2h` (L/h≥1) | `Qp ≈ 1 + μL/(2h_m)` is the standard Ekelund/Sims mean-pressure "friction-hill" approximation used throughout the hot-rolling force literature | Recognised textbook approximation (Lenard, *Primer on Flat Rolling*; Roberts) — not independently re-fetched, treated as well-established | **CONSISTENT** | governs F together with flow stress |
| 18 | Bite condition `tan(α_max)=μ`; `Δh=D(1-cos α_max)` exact vs. `Δh=μ²R` approx, `:124-142` | exact + approx both coded | Standard self-acting-bite condition, universal in rolling-mechanics texts; the model's own comment that the small-angle form overstates the limit is arithmetically correct (verified: 4.66% at μ=0.25, not "about 4%" as the docstring rounds — flagged already by the transmission audit as a P2 item, not re-litigated here) | Textbook geometry (Lenard; Roberts) | **CONSISTENT / FACT** (geometry, not empirical) | sets the deepest permissible draft per pass |
| 19 | `PLANE_STRAIN_FACTOR` = 2/√3 = 1.1547, `:271` | 1.1547 | Exact von Mises plane-strain constraint factor `k = (2/√3)σ`; standard result in metal-forming mechanics | DoITPoMS TLP "Plane strain" (Cambridge teaching resource) — page fetch blocked (403) but the identity is standard continuum-plasticity mechanics, reproduced in every rolling-mechanics text (Lenard; Hosford & Caddell) | **CONSISTENT / FACT** (exact mechanics identity) | +15% on all wide-pass loads (b/h≥5), as the model itself states |
| 20 | `ETA_GEARBOX/PINION/SPINDLE/COUPLING` = 0.97/0.98/0.99/0.995, `:458-460,772` | as coded | Helical-gear-stage efficiency 97–99%, universal-spindle and gear-coupling efficiency 98–99.8% are standard mechanical drive-train figures | Generic mechanical-drivetrain engineering practice (not independently re-sourced to a named handbook within budget) | **CONSISTENT** | sets 0.899 overall chain efficiency, cross-checked and reproduced exactly in `TRANSMISSION_AUDIT_STEEL_2026-09-26.md` §2 |
| 21 | `SERVICE_FACTORS.application_factor` = 1.75, `:466` | 1.75 | "Heavy shock, uniform driver" steel-mill service factors are reported in general gearbox-selection literature as ~1.75–2.5 | IGS Gear, "How to Select Service Factors for Industrial Gearboxes" (secondary/marketing source, CLAIM) | **EDGE** — sits at the low end of the cited range | +43% possible if raised to 2.5 (see §2) |
| 22 | `SERVICE_FACTORS.reversing_factor` = 1.15, `:468` | 1.15 | AGMA's fully-reversing-load derating for gear teeth (idler/planet-type reversal) is commonly quoted as a **0.70** allowable-stress multiplier — mathematically equivalent to inflating required rating by **1/0.70 ≈ 1.43×**, i.e. noticeably higher than 1.15 | Gear Solutions, "New Refinements to the Use of AGMA Load Reversal and Reliability Factors" (secondary trade article citing AGMA practice — CLAIM) | **EDGE / possibly UNDERSTATED** — the analogy (idler-gear full reversal vs. a reversing mill main drive) is not exact, so this is flagged, not asserted as wrong | quantified in §2: does **not** change the governing gearbox criterion in this project (bite-shock still governs) |
| 23 | `SERVICE_FACTORS.thermal_factor` = 1.00, `:470` | 1.00, conditional on forced-circulation oil cooling | Standard practice: thermal derating is 1.0 only with adequate cooling; correctly stated as conditional by the model itself | — | **CONSISTENT** (conditional ASSUMPTION, correctly flagged) | — |
| 24 | `BITE_SHOCK_RANGE` = (2.0, 3.0), `:474` | 2×–3× steady torque | A bite-impact factor of order 2–3× steady rolling torque is a commonly cited rule of thumb in mill-drive design texts (Ginzburg-type sources); I could not pin an exact primary citation within budget | — | **UNSOURCED** (plausible order of magnitude) | this is the criterion that **governs** the gearbox rating in the current schedule (TRANSMISSION_AUDIT §2) — the single highest-leverage unsourced number in the drive train |
| 25 | `GEARBOX_PEAK_ALLOWANCE` = 2.0, `:475` | 2.0 | Manufacturer catalogues commonly allow ~2× rated torque for short-duration peaks; genuinely manufacturer-specific | — | **CONSISTENT** (industry-typical, but manufacturer-specific by nature — correctly left open in Package A as [RDR]) | directly sets the governing gearbox torque, per §24 |
| 26 | `STANDARD_RATIOS` (3.15…25.0), `:477` | ISO R20-type preferred numbers | Exact match to the ISO 3 preferred-number R20 series | ISO 3 preferred numbers — FACT (standard, not re-fetched) | **CONSISTENT / FACT** | — |
| 27 | `commutation_overload_limit` 2.0×→1.2× linear fall to 3× base speed, `:855-869` | as coded | Qualitatively correct (DC commutation ceiling falls with field-weakening speed) per general DC-machine theory; the specific numbers (2.0, 1.2, linear) are the model's own stated ASSUMPTION pending a vendor curve — no IEEE/IEC numeric curve was found to confirm or refute the specific figures within budget | Generic DC-motor field-weakening discussion (forum-level sources only reached; no IEEE/IEC standard curve retrieved) | **UNSOURCED** (direction correct, magnitude unconfirmed) | this is the check that rejected the 1:12.5 ratio and drove the 1:7.1 redesign — the single highest-leverage unsourced number in the motor selection, exactly as the model's own docstring says |
| 28 | `inertia_at_motor_kgm2` default `motor_rotor_j=400`; Package A range 250/450/750 kg·m² for a ~1600 kW/350 rpm DC mill motor | 250–750 kg·m² | No manufacturer nameplate or handbook figure was retrieved within budget for a machine of this rating; order of magnitude (hundreds of kg·m²) is plausible for a large low-speed DC mill motor but unconfirmed | — | **UNSOURCED** (already correctly held as a Hold Point in Package A / ENGSPEC) | governs regen power (675–1012 kW) and reversal commutation utilisation — both already flagged as open in the transmission audit |
| 29 | `MILL_MODULUS_MN_PER_MM` = (3.0, 8.0), `:634` | 3–8 MN/mm | No literature figure retrieved within budget for a two-high stand of this barrel size; the model's own docstring already treats this correctly as UNKNOWN pending a half-day closed-rolls test | — | **UNSOURCED** | governs thickness control only (`stand_stretch_mm`), not force/torque/power |
| 30 | Ar3 ≈ 820–850 °C (Package A §2.2, not a `.py` constant) | 820–850 °C, ESTIMATE | (a) Commonly cited approximate range for plain low-C, C-Mn structural steel in TMCP/hot-rolling literature is close to this band (CLAIM, general); (b) a published regression `Ar3 = 914 − 6.85·CR − 650·C − 134·Mn + 179·Si` (for a different, Nb-microalloyed pipeline-steel family, cooling rates 1–15 °C/s) gives **≈630 °C** for an S355JR-like composition (C≈0.20, Mn≈1.4, Si≈0.25) at a slow ~1–2 °C/s interpass cooling rate | (a) generic hot-rolling/TMCP literature, not independently pinned to one primary source within budget; (b) IOP Conf. Series 283 (2018) 012024, regression derived for a different steel family — CLAIM, extrapolation outside its fitted domain is doubtful | **EDGE** — two sources disagree by ~200 °C, and neither is chemistry-matched to S355JR/S235JR with this mill's actual cooling rate | Directly decides the phase-1/phase-2 boundary (12 mm "borderline," 10 mm+ "reject" in Package A) — this is the second most consequential unresolved item after the flow-stress anchors |
| 31 | Roll-neck allowable stress by material (no model constant — only `neck_bending_stress_mpa()` computes the *actual* stress, 181–213 MPa across scenarios) | not coded as a limit | No two independent, chemistry/heat-treatment-specific allowable-stress figures were found within budget. A general "safety factor ≈5" was found for rolling-mill rolls generally (single secondary source), not a bending-stress number, and not broken out by cast iron vs. forged steel | SME Group blog (single secondary source, safety-factor statement only) | **UNSOURCED** | the project's own withdrawal of Package B's premature "181–213 MPa is rejected for cast iron" verdict (TRANSMISSION_AUDIT M14) is the technically correct call — no allowable-stress figure exists yet to test against, because roll material is itself an open Hold Point |
| 32 | S235JR/S355JR chemistry cited in `GRADES` docstring (C 0.17/0.24, Mn 1.40/1.60 max) | as coded | Matches the nominal EN 10025-2 composition limits for these grades | EN 10025-2 (standard; not re-fetched, treated as textbook FACT) | **CONSISTENT / FACT** | basis for item 15 only |

---

## 2. Sensitivity notes (computed locally against a throwaway, unmodified copy of `slab_line_design.py`; nothing in the repo was changed)

All figures below are `build_schedule(12.0, scenario, grade="S355JR")` (12 mm is the
declared phase-1 floor), governing pass only.

**Friction, μ 0.25 → 0.35** (task's own worked example, reproduced exactly):
| Scenario | μ | max F | max T (roll) | max P |
|---|---|---|---|---|
| conservative | 0.25 | 3.217 MN | 96.0 kN·m | 960 kW |
| balanced | 0.30 | 3.477 MN | 127.7 kN·m | 1277 kW |
| aggressive | 0.35 | 3.988 MN | 169.9 kN·m | 1699 kW |

0.25→0.35 is **+8.7% on peak force** but a much larger swing on torque/power at fixed
target thickness, because a higher μ also changes the pass count (13→9→7 passes) and
therefore which pass governs — μ is not a simple linear knob on this schedule the way
it is on a single fixed pass. Bite limit (`max_draft_bite_mm`) scales exactly as μ²:
18.75 → 27.0 → 36.75 mm friction-limited draft (small-angle form) across the same μ
range, i.e. **+96% bite capacity** from 0.25→0.35, which is why the pass count falls
so much — this is the single most schedule-shaping assumption in the model, confirming
the model's own docstring emphasis on μ as "the most consequential assumption here."

**Flow stress ±15%, single pass, all else fixed** (isolates the pure linear effect):
| Case | Force | Torque (roll) |
|---|---|---|
| −15% | −15.0% (2.955 MN) | −15.0% (104.6 kN·m) |
| +15% | +15.0% (3.998 MN) | +15.0% (141.5 kN·m) |

Exactly linear, as expected from `F = Q·σ·b·L_c` with Q and geometry unaffected by σ.
Power scales with torque at fixed speed, so also exactly ±15%. **This means the
flow-stress anchor values (item 14) translate one-for-one into force/torque/power
uncertainty** — an unresolved ±15–20% question there is not attenuated anywhere
downstream.

**Service factor, reversing_factor 1.15 → 1.43** (item 22's AGMA-implied figure):
total service factor 2.2138 → 2.7532 (+24.4%); criterion A (`rms·SF`) rises from
175.1 to ~217.9 kN·m at the rolls — still below criterion B (bite-shock/2 = 327.4
kN·m), which continues to govern. **Conclusion: even a materially higher reversing
factor does not change the gearbox rating recommendation in this specific schedule**,
because the bite-shock criterion already dominates by a wide margin. This is a useful,
low-cost finding: item 22's uncertainty is real but does not propagate to the
headline gearbox number.

**Application factor 1.75 → 2.5** (top of the cited "steel mill" range, item 21):
total service factor 2.2138 → 3.1626 (+42.9%); criterion A rises to ~250.2 kN·m —
still below the 327.4 kN·m bite-shock criterion. **Same conclusion as above: the
governing criterion is bite-shock, not fatigue, across the plausible range of both
disputed service-factor terms.** The real leverage in the drive train is therefore
squarely on `BITE_SHOCK_RANGE` (item 24) and `commutation_overload_limit` (item 27),
both UNSOURCED.

**Ar3 disagreement (item 30):** the model doesn't compute Ar3 itself (no `.py`
constant), so there is no function to re-run; the effect is entirely in Package A's
manual pass/fail table. If ~630 °C (the pipeline-steel regression) is closer to the
true value for this composition than 820–850 °C, every schedule down to 6 mm (finish
673 °C) would newly appear thermally acceptable, reversing today's phase-1/phase-2
split. If the higher literature band is right, today's split stands. This is exactly
why item 30 is flagged EDGE rather than resolved either way — the two candidate
values are 200 °C apart and neither is chemistry-matched to this steel.

---

## 3. Proposed regression tests (not written into the repo)

| # | Benchmark | Source | Expected value | Tolerance | Model function to call |
|---|---|---|---|---|---|
| 1 | Shida (1969) flow-stress table point for a plain low-C steel at a stated (T, ε̇, ε) | Shida (1969), primary paper (not yet obtained) | published σ̄ at that point | ±10% (typical scatter of this correlation family) | `flow_stress_mpa(temperature_c, strain_rate_s, strain, grade="S235JR")` |
| 2 | Misaka & Yoshimoto (1967) flow-stress point, same conditions as #1 | Misaka & Yoshimoto (1967) | published σ̄ | ±10% | same, cross-checked against #1 for the ±15–20% band the two correlations typically span |
| 3 | Sims (1954) worked roll-force example (a published input/output geometry + force result) | Sims (1954), *Proc. IMechE* 168:191 | published F | ±15% (accounts for Sims' own simplifications vs. this model's Q_p form) | `flow_stress_mpa(...)` → `geometry_factor(...)` → `F = Q·σ·b·L_c` (manual composition of the pieces `build_schedule` uses internally) |
| 4 | El-Kalay & Sparling (1968) or Wusatowski-tabulated spread example, matched b₀/h₀ and h₀/D | El-Kalay & Sparling (1968), *J. Iron Steel Inst.*; Wusatowski (1969) | published exit width | ±15% (model's own docstring already claims ±10–20% scatter) | `wusatowski_exit_width_mm(entry_h, exit_h, entry_b)` |
| 5 | Bite-limit geometry: any published (μ, D, Δh_max) triple used as a textbook worked example | Lenard, *Primer on Flat Rolling*, or Roberts, *Hot Rolling of Steel* (worked examples) | published Δh_max | exact (pure geometry, no scatter expected) | `max_draft_bite_exact_mm(mu, roll_diameter_mm)` |
| 6 | AGMA 6015-A13 (**"Power Rating of Single and Double Helical Gearing for Rolling Mill Service"** — the standard actually written for this application, not the generic 6011/6013 named in the brief) worked service-factor example for a reversing mill drive | ANSI/AGMA 6015-A13 | published required rating | ±10% | `total_service_factor()`, `gearbox_rating_trace(...)` |
| 7 | A published DC-motor commutation-limit curve (Siemens or ABB application note, or IEEE paper) at a stated field-weakening ratio | Siemens/ABB DC drive application note (not yet obtained); IEEE Trans. Industry Applications, DC commutation literature | published overload ceiling at that speed ratio | ±10% | `commutation_overload_limit(motor_rpm, base_rpm, ...)` |
| 8 | A CCT-diagram or dilatometry Ar3 value for an actual S355JR/S235JR heat chemistry at a cooling rate representative of this mill's interpass times (≈1–5 °C/s) | ASM Atlas of Continuous Cooling Transformation Diagrams, or a certified mill test certificate + CCT reference | published Ar3 | ±20 °C | not a model function (Ar3 is not coded); would inform a new, explicit `AR3_C` constant if added later |
| 9 | Neck bending-stress allowable for a named roll material (e.g. forged 45CrNiMoV-type roll steel, or a named cast-iron grade), from a roll-manufacturer datasheet or a rolling-mill mechanical-design handbook (Ginzburg) | Ginzburg, *Steel-Rolling Technology*, or a roll OEM datasheet (not yet obtained) | published allowable bending/fatigue stress | ±15% | `neck_bending_stress_mpa(force_n, neck_diameter_mm, offset_mm)` — compare the computed 181–213 MPa against the published allowable once roll material is known |
| 10 | Bite-shock impact factor for a reversing mill main drive, from a named mill-drive design reference (Ginzburg, or a gearbox OEM mill-duty guide) | Ginzburg, *Steel-Rolling Technology*, or Flender/Renk mill-duty application guide (not yet obtained) | published impact factor range | should bracket 2.0–3.0 | `torque_chain(...).bite_shock_low_nm / .bite_shock_high_nm` |

---

## 4. Reading list

Already cited in the repo's own registers (not duplicated in full here — see
`ROLLING_MILL_ENGINEERING_REFERENCE_KNOWLEDGE.md` §Sources and
`PRIOR_ART_AND_BENCHMARK_REGISTER.md` §PA-002 for the spread-model list):
Misaka & Yoshimoto (1967); Shida (1969); Sims (1954); El-Kalay & Sparling (1968);
Wusatowski (1969); Said et al. (1999); Wang et al. (2019, ISIJ International).

Newly identified in this pass, not yet in the repo registers:
- **ANSI/AGMA 6015-A13**, *Power Rating of Single and Double Helical Gearing for
  Rolling Mill Service* — this is the standard actually written for mill gearing, and
  should replace or supplement the brief's reference to the generic AGMA 6011/6013.
  https://webstore.ansi.org/standards/agma/ansiagma6015a13
- Ekelund's two-branch friction formula, as quoted (secondhand) in a Sheffield Hallam
  thesis reviewing Roberts: μ = 0.6 − 0.0005T (cast iron/rough rolls) and
  μ = 0.5(1.05 − 0.0005T) (chilled/smooth steel rolls), T in °C — flagged CLAIM; the
  numbers look low at slab-mill temperatures (near-zero at 1200 °C) and should be
  checked against Roberts' primary text before use.
  https://shura.shu.ac.uk/19698/1/10696998.pdf
- Gear Solutions, "New Refinements to the Use of AGMA Load Reversal and Reliability
  Factors" (trade article citing AGMA reversal-derating practice, 0.70 factor).
  https://gearsolutions.com/features/new-refinements-to-the-use-of-agma-load-reversal-and-reliability-factors/
- IOP Conf. Series: Materials Science and Engineering 283 (2018) 012024 — Ar3
  regression `914 − 6.85·CR − 650·C − 134·Mn + 179·Si`, fitted to a Nb-microalloyed
  pipeline-steel family; applicability to S355JR/S235JR at this mill's cooling rates
  is unverified and should not be used without checking the fitted composition/rate
  domain. https://iopscience.iop.org/article/10.1088/1757-899X/283/1/012024/pdf
- Transmetra emissivity compilation (oxidised iron 0.85–0.89; rough ingot iron
  0.87–0.95). https://www.transmetra.ch/images/transmetra_pdf/publikationen_literatur/pyrometrie-thermografie/emissivity_table.pdf

Not obtained within this pass (primary texts named in the brief that remain to be
sourced directly, ideally from a library rather than the open web, per the existing
register's own finding that this equipment class is "archive work, not web work"):
Lenard, *Primer on Flat Rolling*; Ginzburg, *Steel-Rolling Technology*; Roberts,
*Hot Rolling of Steel* (full text); Tselikov (any English-language edition); the
primary Shida (1969) and Misaka & Yoshimoto (1967) papers themselves (only secondary
citations of them were reached); any Siemens/ABB DC drive application note giving a
numeric commutation-overload curve.
