# Rolling Mill Engineering — General Reference Knowledge Base

Status: LITERATURE / GENERIC ENGINEERING SCIENCE ONLY. Nothing in this file is a fact
about the `rolling_mill_strip_300_pilot` line. It exists so that once real, verified
plant data clears the `rolling_mill_intake.py` gate, calculation work in
`rolling_mill_mechanics.py` has calibration-ready starting points instead of starting
from zero — it does not shortcut, weaken, or bypass that gate in any way.

Per `.nexus/expert_foundry/MASTER_PROMPT_v0.1.md` and the project's evidence
discipline: everything below is classified `FACT` only about the *cited published
correlation itself* (i.e. "Shida published this equation in this paper") — applying
any of it to this specific mill's actual grade, temperature and equipment is an
`ASSUMPTION` until calibrated against this plant's own measured data (see
"Calibration protocol" at the end). No numeric constant here is to be copied into a
project calculation as a default.

## 1. Flow stress models (mean flow stress, MPa)

Needed for `estimate_pass_force`'s `flow_stress_model` parameter. None of these are
wired into the codebase — they are candidate starting points for calibration.

- **Misaka & Yoshimoto (1967)** — empirical hot-flow-stress correlation for plain
  carbon steel as a function of carbon content, strain, strain rate and temperature.
  Widely cited baseline for carbon-steel hot rolling; needs the steel's actual %C
  (project's own claim reads "St37" — a general structural low-carbon grade family,
  but the exact chemistry certificate has not been supplied and must not be assumed).
- **Shida (1969)** — alternative empirical correlation, similar inputs, often quoted
  alongside Misaka-Yoshimoto as a cross-check pair in mill-modeling literature.
- **Hensel-Spittel type equations** — general power-law form
  `kf = A * exp(m1*T) * eps^m2 * eps_dot^m3 * ...`, commonly fitted per-grade from lab
  compression/torsion tests; the coefficients are grade- and lab-specific and are not
  transferable without a certificate or a plant-run fit.

None of these can be used responsibly here without: (a) a confirmed chemistry/grade
certificate, and (b) a temperature range consistent with this line's actual reheat
practice (currently an open, unanswered item — `process.reheating_temperature_degC`
is still missing in the intake contract).

## 2. Friction models

Needed for the `friction_coefficient` parameter and the biting-condition check.

- **Ekelund (1927)** — friction coefficient as a function of temperature and roll
  surface condition (a widely cited historical baseline for hot rolling).
- **Siebel** — alternative friction estimate, also temperature/surface dependent.
- Typical hot-rolling friction coefficients cited in textbooks span roughly 0.2–0.5
  depending on roll surface condition (rough cast iron vs. ground/lubricated), scale
  conditions, and temperature — this range is cited only to show why a single
  "textbook default" would be irresponsible to hardcode; the actual roll surface
  condition and any lubrication practice on this line have not been described by the
  engineer yet.

## 3. Spread (width-increase) models

Needed for `estimate_spread_mm`'s `spread_model` parameter — directly relevant to
this project since the entire question is whether a 150 mm billet can be widened
toward a 300 mm target through some pass sequence.

- **Sims (1954)** — one of the original analytical spread treatments alongside his
  force/torque work already cited in `rolling_mill_mechanics.py`.
- **El-Kalay & Sparling (1968)** — empirical spread formula widely used for hot
  flat/plate rolling, function of draft, width-to-thickness ratio and roll diameter.
- **Wusatowski** — compiled multiple empirical spread formulas (Sims, Sedláček,
  Beese, etc.) in *Fundamentals of Rolling* (1969), a standard reference text for
  exactly this kind of billet/bar/strip spread estimation.

**Critical caveat specific to this project**: none of these classical spread formulas
were derived for a *3-high, multi-stand roughing train feeding a finishing train*
producing a specific discrete width target from a square billet — they are closer
approximations for a single flat pass. Any spread estimate here would need validation
against this line's own historical width-in/width-out pass data (still an open,
requested item — see the historical-run request in the questionnaire already sent).

## 4. Biting condition and roll-grip limits

Already implemented exactly (not an approximation) in `rolling_mill_mechanics.py`:
`tan(bite_angle) <= friction_coefficient`. This is genuinely useful the moment a
credible friction coefficient range is chosen (see §2) — it can flag, for any
candidate draft/roll-radius combination, whether the pass is even geometrically
capable of self-feeding, independent of any force/torque uncertainty. This check
requires no material assumption beyond friction, so it is the safest of the
material-dependent tools to exercise early once §2 has an evidence-backed number.

## 5. Cross-checks against real equipment limits (already usable once nameplate data exists)

`compare_power_with_motor_rating()` in `rolling_mill_mechanics.py` is a pure
consistency check (estimated power vs. nameplate rating) — it does not need a
material model to be useful as a *sanity bound*: once a historical run's actual motor
current draw is known (`measured_motor_current_a` field already exists in
`HistoricalPass`), it can be cross-checked against nameplate current
(`limits.maximum_motor_current_a`, currently missing) independent of any flow-stress
assumption. This is the single most evidence-cheap calculation path available once
the questionnaire's remaining nameplate/limits items come back.

## Calibration protocol (mandatory before any of the above is trusted)

1. Confirm actual chemistry/grade certificate for the billet material (not just the
   spoken label "St37").
2. Confirm actual reheat temperature practice (currently missing from the intake).
3. Obtain at least one historical successful pass record (input/output thickness,
   width, roll speed, temperature, and ideally measured motor current) — already
   requested from the engineer.
4. Fit/select a flow-stress model and friction coefficient against that historical
   record — i.e. solve backwards for what constant makes the model reproduce the
   *known, verified* historical outcome — rather than importing a textbook constant
   as truth.
5. Only after step 4 succeeds does a flow-stress/friction pairing become a
   `CALIBRATED` model suitable for `estimate_pass_force`. Until then, every entry in
   §1–§3 remains classified `HYPOTHESIS` (a plausible starting point from literature),
   never `FACT` about this mill.

## Sources

- Misaka, Y. & Yoshimoto, T. (1967). Hot deformation resistance correlation for
  carbon steels (widely cited baseline; original in Japanese, summarized in
  subsequent English-language rolling textbooks).
- Shida, S. (1969). Empirical formula of flow stress of carbon steels — resistance
  to deformation of carbon steels at elevated temperature.
- Sims, R.B. (1954). "The Calculation of Roll Force and Torque in Hot Rolling
  Mills." Proc. IMechE. https://doi.org/10.1243/PIME_PROC_1954_168_023_02
- El-Kalay, A.K.E.A. & Sparling, L.G.M. (1968). Spread formula for hot flat rolling.
  J. Iron Steel Inst.
- Wusatowski, Z. (1969). *Fundamentals of Rolling*. Pergamon Press.
- Said, A. et al. (1999). "The temperature, roll force and roll torque during hot
  bar rolling." J. Materials Processing Technology.
  https://doi.org/10.1016/S0924-0136(98)00391-4
- Wang et al. (2019). Data-driven roll force/torque parameter families.
  https://doi.org/10.2355/isijinternational.ISIJINT-2018-846

## 6. Terminology precision (added 2026-09-17, grounded via literature/industry-reference check)

These distinctions matter directly for resolving this project's open ambiguous claims
(barrel length "1350" vs the confirmed 1280mm ST1 barrel; "450 to 480" roll diameter):

- **Roll barrel (body)**: the cylindrical working section of the roll that actually
  contacts the strip/billet. Barrel length and barrel diameter are the two dimensions
  most often quoted informally as "the roll size" — but informally quoted numbers do
  not specify which of the two, or which stand, unless stated.
- **Roll neck / journal**: the reduced-diameter section at each end of the roll that
  sits in the bearing/housing — a different (usually much smaller) diameter than the
  barrel, and never to be confused with it when a bare number like "450" is given.
- **Overall roll (shaft) length**: barrel length **plus** both necks — a larger number
  than barrel length alone. If a claimed length doesn't match a confirmed barrel
  length, checking whether it's actually the overall shaft length is the first thing
  to ask, before assuming a transcription error or a different stand.
- **Gearbox ratio vs. rated output torque**: these are two independent nameplate
  fields. A ratio (e.g. "1:9.8") says nothing about how much torque the gearbox can
  safely deliver — that is a separate, explicitly stated rating, usually in Nm or
  kNm, and must be read off the nameplate/catalog directly, never inferred from the
  ratio alone.
- **This line's actual scale**: worth noting explicitly so nothing here gets
  miscalibrated against the wrong reference class — general rolling-mill literature
  (e.g. large slab-mill roughing trains) often quotes roll diameters "near 1000 mm."
  This project's mill is a much smaller merchant-bar/billet-to-strip line (150mm
  square billet in, roll diameters in the 450-520mm range) — that scale is entirely
  ordinary for a small mill and should not be treated as implausible just because it
  differs from large-slab-mill figures; the two are different equipment classes.

## 7. Nameplate/document reading checklist (added 2026-09-17)

For requesting or interpreting future evidence from this line, the complete field
lists worth asking for (not just "send a photo of the plate"):

**Motor nameplate**: rated power (kW/HP), rated speed (rpm), voltage (V), full-load
current (A), frequency (Hz), service factor, insulation class, duty rating, frame/NEMA
design (if present).

**Gearbox nameplate**: manufacturer, model/serial number, gear ratio, input speed,
output speed, **rated (continuous) output torque with its unit** (Nm/kNm — this is a
distinct field from the ratio and is very often the missing piece in informally
relayed equipment descriptions), service factor, approved mounting position,
lubricant spec.

## 8. Additional citation

- A New Model for Predicting Width Spread in a Roughing Mill (2014), J. Soc. Naval
  Architects/journal reference — an additional data-driven spread-model reference
  alongside Sims/El-Kalay/Wusatowski in §3, useful once real pass data exists to fit
  against.

## Sources (additions)

- VFDs.com, "How to Read a Motor Nameplate": https://vfds.com/blog/how-to-read-a-motor-nameplate/
- WorldWide Electric, "Electric Motors: How to Read the Nameplate":
  https://worldwideelectric.com/articles/electric-motors-how-to-read-the-nameplate/
- Industrial Gearbox Solutions, "How to Read a Gearbox Nameplate":
  https://industrialgearboxsolutions.com/how-to-read-a-gearbox-nameplate/
- ScienceDirect Topics, "Roughing Mill": https://www.sciencedirect.com/topics/engineering/roughing-mill
- steelnumber.com, St37-2 / EN 10025 equivalence table:
  http://www.steelnumber.com/en/equivalent_steel_iron_eu.php?zname_id=161
