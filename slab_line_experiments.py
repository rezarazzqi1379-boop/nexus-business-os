"""Read-only what-if experiment harness for the slab-line feasibility model.

THIS IS SENSITIVITY ANALYSIS ON A CONCEPT MODEL. Every number this module
prints or writes is a computed consequence of an INPUT ASSUMPTION being
perturbed within (or just outside) its stated literature range. Nothing here
is an operating setpoint, a pass schedule, a recipe, or a trial instruction —
see `docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md` for the evidence
class and range of every constant this module touches, and `AGENTS.md` /
`CLAUDE.md` for the two-gate rule (concept calculation permitted, release is
not).

The question this module answers: "if an uncertain input is off, which
headline results and which vendor-facing numbers move, and by how much?"

Design
------
- stdlib only. Does NOT import `pytest`, does NOT modify `slab_line_design.py`.
- Every perturbation is restored, always, via one of two mechanisms:
    1. `override_constants()` — a context manager that temporarily replaces a
       `slab_line_design` module attribute (e.g. the whole `SCENARIOS` dict,
       or `FS_A`) and puts the *exact original object* back in `finally`,
       even when the wrapped block raises. This is safe because every
       constant touched here (`SCENARIOS`, `FS_A`, `GRADES`) is read by
       `slab_line_design`'s own functions as a bare global name AT CALL TIME
       (Python resolves it against the module's `__dict__`, i.e. this same
       object), never as a value already baked into a function's bytecode.
       Constants that are instead only used as function DEFAULT ARGUMENTS
       (e.g. `roll_diameter_mm: float = ROLL_DIAMETER_MM`) are bound once at
       `def` time and would NOT observe an attribute override — none of the
       experiments below touch such a constant for this reason.
    2. Plain function arguments the model already accepts (`grade=`,
       `motor_rotor_j=`, `accel_time_s=`, `decel_s=`) — no override needed.
- Experiments are DATA: `EXPERIMENTS` is a flat list of `Experiment` records
  (id, parameter, values, basis_note, literature_ref). The logic that knows
  how to *run* each experiment id lives in ordinary functions below, keyed by
  the same id — the dataclass itself carries no callables.

Fragility linkage (task item 3)
--------------------------------
For every claim in `nexus_checks.transmission.CLAIMS` (the "model"-sourced
ones only — `CLAIMS_INPUT` has no model function behind it and is skipped),
this module recomputes the claim's expected value under each experiment
value and compares the ROUNDED value (using the claim's own `round` rule —
the same rounding a vendor document would show) against the rounded value at
the TRUE, unperturbed model state (i.e. the state that matches the actually
committed RFIs). This is deliberately independent of `claim.tol`, which
exists for a different purpose (float noise between the model's raw output
and a document's already-rounded text) and is not a meaningful yardstick for
a real physical perturbation. Classification:
    stable  - rounded value identical to the nominal rounded value
    moves   - rounded value differs, by less than 25% relative change
    breaks  - rounded value differs by >=25%, or recomputation raises
Two claims (`regen-680-at-3s`, `accel-torque-12-29`) hardcode their own
rotor-inertia / ramp-time basis as literals inside `transmission.py` itself
(these are exactly the quantities under test in the `rotor-inertia` and
`ramp-time` experiments) rather than reading a `slab_line_design` module
constant, so for those two experiment IDs only, this module recomputes the
claim's own formula directly with the swept argument in place of the
literal, calling the same `slab_line_design` functions the claim itself
calls. Every other (experiment, claim) pair goes through the real
`claim.compute(model)` unchanged, against whichever module attribute the
experiment has perturbed — this is what makes the fragility matrix track a
change to `slab_line_design.py` itself, not a copy of its logic.
"""
from __future__ import annotations

import argparse
import contextlib
import datetime
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import slab_line_design as model  # noqa: E402  (path insert must come first)
from nexus_checks import transmission as txm  # noqa: E402

# ---------------------------------------------------------------------------
# restoration primitive
# ---------------------------------------------------------------------------
_SENTINEL = object()


@contextlib.contextmanager
def override_constants(mod, **overrides):
    """Temporarily set module-level attributes on `mod`, restoring the exact
    previous object (or removing the attribute if it did not exist before)
    in `finally` — including when the wrapped block raises. This is the only
    mechanism this file uses to perturb `slab_line_design`; the module's own
    source is never edited."""
    saved = {name: getattr(mod, name, _SENTINEL) for name in overrides}
    try:
        for name, value in overrides.items():
            setattr(mod, name, value)
        yield mod
    finally:
        for name, old in saved.items():
            if old is _SENTINEL:
                delattr(mod, name)
            else:
                setattr(mod, name, old)


# ---------------------------------------------------------------------------
# experiments are data
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Experiment:
    id: str
    parameter: str
    values: tuple
    basis_note: str
    literature_ref: str


EXPERIMENTS: list[Experiment] = [
    Experiment(
        id="friction-mu",
        parameter="MU — friction coefficient used for the bite limit and the "
                  "'balanced' schedule (slab_line_design.py:45, SCENARIOS['balanced']['mu'])",
        values=(0.20, 0.25, 0.30, 0.35, 0.40),
        basis_note="0.25-0.35 is the literature range for hot flat rolling "
                   "(Roberts/Ekelund, per MODEL_LITERATURE_VALIDATION item 1); "
                   "0.20 and 0.40 are edge cases outside that range. Nominal "
                   "'balanced' value is 0.30.",
        literature_ref="docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 1; "
                       "slab_line_design.py:45-50",
    ),
    Experiment(
        id="flow-stress-scale",
        parameter="Flow-stress anchor scale factor on FS_A "
                  "(slab_line_design.py:70, the sigma=A*exp(-beta*T)*... anchor)",
        values=(0.85, 1.00, 1.15),
        basis_note="the flow-stress anchor numbers (65/88/120/163 MPa at 1200-900 C) are "
                   "UNSOURCED for their exact values (item 14): the literature check could "
                   "not independently confirm them against a published Shida/Misaka table "
                   "point. +-15% brackets that unresolved uncertainty; the model's own "
                   "sensitivity note already shows this scales force/torque/power exactly "
                   "1:1.",
        literature_ref="docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 14 and "
                       "section 2; slab_line_design.py:67-70",
    ),
    Experiment(
        id="grade",
        parameter="Steel grade flow-stress multiplier (slab_line_design.py:72-78, GRADES)",
        values=("S235JR", "S355JR"),
        basis_note="S355JR carries a +15% flow-stress multiplier over S235JR from an "
                   "UNSOURCED '~6%/%Mn rule of thumb' (item 15). The vendor RFIs are all "
                   "computed at S355JR (the declared hard case); the transmission fragility "
                   "check for this experiment tests what happens if the true multiplier is "
                   "actually the S235JR one (i.e. the +15% rule is wrong), against those "
                   "S355JR-basis RFI numbers.",
        literature_ref="docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 15; "
                       "slab_line_design.py:72-78",
    ),
    Experiment(
        id="rotor-inertia",
        parameter="motor_rotor_j — rotor (+ drive-train) inertia referred to the motor "
                  "shaft, kg*m^2 (slab_line_design.py inertia_at_motor_kgm2 / motor_duty / "
                  "braking_per_stop argument)",
        values=(250.0, 450.0, 750.0),
        basis_note="Package A's plausible range for a ~1600 kW / 350 rpm DC mill motor; "
                   "item 28, UNSOURCED — no manufacturer nameplate or handbook figure was "
                   "retrieved. Governs regen power and reversal commutation utilisation, "
                   "not any rolling-force/torque/power number.",
        literature_ref="docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 28; "
                       "slab_line_design.py inertia_at_motor_kgm2()",
    ),
    Experiment(
        id="ramp-time",
        parameter="Accel/brake ramp time, s (slab_line_design.py motor_duty accel_time_s / "
                  "braking_per_stop decel_s argument)",
        values=(2.0, 3.0, 4.0),
        basis_note="the RFIs bracket 2-3 s for the accel-torque figure and state 3 s for the "
                   "regen-power figure; no single literature citation pins the ramp time — "
                   "it is a drive-train design choice, tested here alongside the 2-4 s "
                   "bracket the vendor documents already span.",
        literature_ref="nexus_checks/transmission.py compute_accel_torque_range / "
                       "compute_regen_680 (2-3 s basis)",
    ),
    Experiment(
        id="ar3-threshold",
        parameter="Ar3 (austenite->ferrite) threshold, C — thermal pass/fail cutoff. NOT a "
                  "slab_line_design.py constant: Ar3 is computed nowhere in the model, only "
                  "compared against here.",
        values=(630.0, 750.0, 820.0, 850.0),
        basis_note="two literature sources disagree by ~200 C (item 30): 820-850 C is the "
                   "commonly cited generic C-Mn/TMCP hot-rolling range; ~630 C comes from a "
                   "published regression fitted to a DIFFERENT (Nb-microalloyed pipeline) "
                   "steel family, extrapolated outside its fitted domain. Neither is "
                   "chemistry-matched to this project's S235JR/S355JR heats. 750 C is an "
                   "interpolated midpoint scenario, not a third literature source.",
        literature_ref="docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md item 30 and "
                       "section 2 (Ar3 disagreement note)",
    ),
]

# nominal / vendor design basis, held fixed unless the experiment itself
# perturbs it
NOMINAL_SCENARIO = "balanced"
NOMINAL_GRADE = "S355JR"          # the grade every checked RFI number uses
NOMINAL_GEAR_RATIO = 7.1          # the model's own preferred ratio (ratio-7.1 claim)
NOMINAL_ROTOR_J = 750.0           # regen-680-at-3s claim's own basis
NOMINAL_RAMP_S = 3.0              # regen-680-at-3s claim's own basis
NOMINAL_MOTOR_RPM = 678.0         # regen-680-at-3s claim's own basis


@dataclass(frozen=True)
class RunConfig:
    scenario: str = NOMINAL_SCENARIO
    grade: str = NOMINAL_GRADE
    gear_ratio: float = NOMINAL_GEAR_RATIO
    rotor_j: float = NOMINAL_ROTOR_J
    ramp_s: float = NOMINAL_RAMP_S
    motor_rpm: float = NOMINAL_MOTOR_RPM


# ---------------------------------------------------------------------------
# per-experiment perturbation: module-constant override (or no-op) used both
# for headline-output computation and for the transmission fragility check
# ---------------------------------------------------------------------------
def _mu_override(mod, mu_value: float):
    base = mod.SCENARIOS[NOMINAL_SCENARIO]
    new_scenarios = dict(mod.SCENARIOS)
    new_scenarios[NOMINAL_SCENARIO] = {**base, "mu": mu_value}
    return override_constants(mod, SCENARIOS=new_scenarios)


def _flow_stress_override(mod, factor: float, nominal_fs_a: float):
    return override_constants(mod, FS_A=nominal_fs_a * factor)


def _grade_multiplier_override(mod, grade_value: str):
    """The vendor RFIs are all computed with grade='S355JR' hardcoded inside
    nexus_checks.transmission's own compute() helpers. To make the 'grade'
    experiment mean something for the fragility check, 'S235JR' here answers
    "what if the true S355JR flow-stress multiplier were actually the
    S235JR one" (i.e. the +15% rule of thumb is wrong) rather than "what if
    the RFIs had been computed for a different grade" (they weren't)."""
    if grade_value == NOMINAL_GRADE:
        return contextlib.nullcontext(mod)
    new_grades = dict(mod.GRADES)
    new_grades[NOMINAL_GRADE] = (mod.GRADES[grade_value][0], mod.GRADES[NOMINAL_GRADE][1])
    return override_constants(mod, GRADES=new_grades)


def experiment_context(mod, experiment: Experiment, value):
    """Context manager applying `experiment`'s module-level perturbation for
    `value`. rotor-inertia, ramp-time and ar3-threshold need no module
    override at all (they are plain function arguments, or not a model
    constant in the first place) so they return a no-op context."""
    if experiment.id == "friction-mu":
        return _mu_override(mod, value)
    if experiment.id == "flow-stress-scale":
        return _flow_stress_override(mod, value, nominal_fs_a=NOMINAL_FS_A)
    if experiment.id == "grade":
        return _grade_multiplier_override(mod, value)
    return contextlib.nullcontext(mod)


NOMINAL_FS_A = model.FS_A  # captured once at import, before anything perturbs it


def run_config_for(experiment: Experiment, value) -> RunConfig:
    if experiment.id == "grade":
        return RunConfig(grade=value)
    if experiment.id == "rotor-inertia":
        return RunConfig(rotor_j=value)
    if experiment.id == "ramp-time":
        return RunConfig(ramp_s=value)
    return RunConfig()


# ---------------------------------------------------------------------------
# headline outputs (task item 2)
# ---------------------------------------------------------------------------
def regen_kw(mod, cfg: RunConfig) -> float:
    j = mod.inertia_at_motor_kgm2(cfg.gear_ratio, motor_rotor_j=cfg.rotor_j)
    return mod.braking_per_stop(j, cfg.motor_rpm, cfg.ramp_s)["instantaneous_power_kw"]


def gearbox_output_required_knm(mod, cfg: RunConfig) -> float:
    s30 = mod.build_schedule(30.0, cfg.scenario, grade=cfg.grade)
    cs = mod.cycle_summary(s30)
    tr = mod.gearbox_rating_trace(s30, cfg.gear_ratio, cs["cycle_s"])
    f = txm._output_factor(mod)
    return tr["rated_requirement_nm"] / f / 1000.0


@dataclass(frozen=True)
class HeadlineResult:
    peak_force_mn: float
    peak_torque_knm: float
    peak_power_kw: float
    gearbox_output_required_knm: float
    regen_kw: float
    accel_brake_per_h_lo: float
    accel_brake_per_h_hi: float
    capacity_tph_lo: float
    capacity_tph_hi: float
    finish_temp_12mm_c: float
    finish_temp_6mm_c: float
    bite_limit_mm: float
    mu_used: float


def compute_headline(mod, cfg: RunConfig) -> HeadlineResult:
    mb = mod.mass_balance()
    peak_force = peak_torque = peak_power = 0.0
    lo_events = hi_events = None
    lo_tph = hi_tph = None
    for t in mod.THICKNESS_TARGETS_MM:
        passes = mod.build_schedule(t, cfg.scenario, grade=cfg.grade)
        wc = mod.worst_cases(passes)
        peak_force = max(peak_force, wc["max_force"].force_n)
        peak_torque = max(peak_torque, wc["max_torque"].torque_roll_nm)
        peak_power = max(peak_power, wc["max_power"].power_kw)
        events = 2 * len(passes) * mb.slabs_per_hour
        lo_events = events if lo_events is None else min(lo_events, events)
        hi_events = events if hi_events is None else max(hi_events, events)
        tph = mod.cycle_summary(passes)["tph"]
        lo_tph = tph if lo_tph is None else min(lo_tph, tph)
        hi_tph = tph if hi_tph is None else max(hi_tph, tph)

    finish_12 = mod.build_schedule(12.0, cfg.scenario, grade=cfg.grade)[-1].exit_temp_c
    finish_6 = mod.build_schedule(6.0, cfg.scenario, grade=cfg.grade)[-1].exit_temp_c
    mu_used = mod.SCENARIOS[cfg.scenario]["mu"]

    return HeadlineResult(
        peak_force_mn=peak_force / 1e6,
        peak_torque_knm=peak_torque / 1e3,
        peak_power_kw=peak_power,
        gearbox_output_required_knm=gearbox_output_required_knm(mod, cfg),
        regen_kw=regen_kw(mod, cfg),
        accel_brake_per_h_lo=lo_events,
        accel_brake_per_h_hi=hi_events,
        capacity_tph_lo=lo_tph,
        capacity_tph_hi=hi_tph,
        finish_temp_12mm_c=finish_12,
        finish_temp_6mm_c=finish_6,
        bite_limit_mm=mod.max_draft_bite_mm(mu_used),
        mu_used=mu_used,
    )


def run_experiment_headline(experiment: Experiment) -> list[tuple[object, HeadlineResult]]:
    """Run every value of `experiment`, restoring model state after each one
    (and after the whole experiment) — the list of (value, HeadlineResult)."""
    rows = []
    for value in experiment.values:
        cfg = run_config_for(experiment, value)
        with experiment_context(model, experiment, value):
            rows.append((value, compute_headline(model, cfg)))
    return rows


# ---------------------------------------------------------------------------
# Ar3 thermal pass/fail classification (task item: not a model constant)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Ar3Row:
    threshold_c: float
    finish_temps: dict  # thickness_mm -> (finish_temp_c, passes_bool)
    n_pass: int


def finish_temperatures(mod, scenario: str = NOMINAL_SCENARIO,
                        grade: str = NOMINAL_GRADE) -> dict:
    """Finish (last-pass exit) temperature at every declared product thickness,
    on the unperturbed design-basis schedule. Ar3 is not computed by the
    model; this only supplies the temperatures Ar3 is compared against."""
    out = {}
    for t in mod.THICKNESS_TARGETS_MM:
        out[t] = mod.build_schedule(t, scenario, grade=grade)[-1].exit_temp_c
    return out


def classify_ar3(finish_temps: dict, threshold_c: float) -> Ar3Row:
    per = {t: (temp, temp > threshold_c) for t, temp in finish_temps.items()}
    n_pass = sum(1 for _, ok in per.values() if ok)
    return Ar3Row(threshold_c, per, n_pass)


def run_ar3_experiment(experiment: Experiment) -> list[Ar3Row]:
    temps = finish_temperatures(model)
    return [classify_ar3(temps, thr) for thr in experiment.values]


# ---------------------------------------------------------------------------
# transmission fragility (task item 3)
# ---------------------------------------------------------------------------
def _recompute_regen(mod, rotor_j: float, ramp_s: float) -> tuple[float]:
    """Mirrors transmission.compute_regen_680's own formula, with the
    literal rotor_j=750 / decel_s=3 it hardcodes replaced by the swept value."""
    r = mod.braking_per_stop(mod.inertia_at_motor_kgm2(7.1, motor_rotor_j=rotor_j),
                             678, ramp_s)
    return (r["instantaneous_power_kw"],)


def _recompute_accel_torque(mod, rotor_j_lo: float, rotor_j_hi: float,
                            ramp_lo: float, ramp_hi: float) -> tuple[float, float]:
    """Mirrors transmission.compute_accel_torque_range's own formula, with
    whichever of (motor_rotor_j, accel_time_s) the experiment sweeps
    substituted for the literals it hardcodes for its low/high case."""
    mb = mod.mass_balance()
    s30 = mod.build_schedule(30.0, "balanced", grade="S355JR")
    cs = mod.cycle_summary(s30)
    lo = mod.motor_duty(s30, 1600, 350, 7.1, cs["cycle_s"], mb.slabs_per_hour,
                        accel_time_s=ramp_lo, max_rpm=700, motor_rotor_j=rotor_j_lo).accel_torque_nm / 1e3
    hi = mod.motor_duty(s30, 2000, 350, 7.1, cs["cycle_s"], mb.slabs_per_hour,
                        accel_time_s=ramp_hi, max_rpm=700, motor_rotor_j=rotor_j_hi).accel_torque_nm / 1e3
    return lo, hi


def recompute_claim(mod, experiment: Experiment, value, claim: txm.Claim) -> tuple[float, ...]:
    """The expected value(s) `claim` would produce under this one experiment
    value. Falls back to the claim's own compute() (against whatever module
    attribute the experiment has perturbed) for every (experiment, claim)
    pair except the two claims that hardcode rotor-inertia / ramp-time as
    literals inside transmission.py itself (see module docstring)."""
    if experiment.id == "rotor-inertia":
        if claim.id == "regen-680-at-3s":
            return _recompute_regen(mod, rotor_j=value, ramp_s=NOMINAL_RAMP_S)
        if claim.id == "accel-torque-12-29":
            return _recompute_accel_torque(mod, rotor_j_lo=value, rotor_j_hi=value,
                                           ramp_lo=3.0, ramp_hi=2.0)
    if experiment.id == "ramp-time":
        if claim.id == "regen-680-at-3s":
            return _recompute_regen(mod, rotor_j=NOMINAL_ROTOR_J, ramp_s=value)
        if claim.id == "accel-torque-12-29":
            return _recompute_accel_torque(mod, rotor_j_lo=450.0, rotor_j_hi=750.0,
                                           ramp_lo=value, ramp_hi=value)
    with experiment_context(mod, experiment, value):
        return claim.compute(mod)


def classify_change(rounded_nominal: tuple[float, ...],
                    rounded_actual: tuple[float, ...], breaks_rel: float = 0.25) -> str:
    if rounded_nominal == rounded_actual:
        return "stable"
    rel = max(abs(b - a) / max(abs(a), 1e-9)
              for a, b in zip(rounded_nominal, rounded_actual))
    return "breaks" if rel >= breaks_rel else "moves"


@dataclass(frozen=True)
class FragilityCell:
    experiment_id: str
    value: object
    claim_id: str
    nominal: tuple
    actual: tuple
    verdict: str  # stable | moves | breaks
    error: str | None = None


def run_transmission_fragility(experiment: Experiment) -> list[FragilityCell]:
    """One FragilityCell per (value, model claim) pair. `CLAIMS_INPUT`
    entries (no model function behind them) are skipped entirely — they are
    not derived from slab_line_design and there is nothing to recompute."""
    out: list[FragilityCell] = []
    for claim in txm.CLAIMS:
        nominal_raw = claim.compute(model)
        nominal_rounded = tuple(claim.round(x) for x in nominal_raw)
        for value in experiment.values:
            try:
                actual_raw = recompute_claim(model, experiment, value, claim)
                actual_rounded = tuple(claim.round(x) for x in actual_raw)
                verdict = classify_change(nominal_rounded, actual_rounded)
                out.append(FragilityCell(experiment.id, value, claim.id,
                                         nominal_rounded, actual_rounded, verdict))
            except Exception as exc:  # noqa: BLE001 - a broken perturbation is itself a finding
                out.append(FragilityCell(experiment.id, value, claim.id,
                                         nominal_rounded, (), "breaks", error=str(exc)))
    return out


def worst_verdict(cells: list[FragilityCell]) -> str:
    order = {"stable": 0, "moves": 1, "breaks": 2}
    return max(cells, key=lambda c: order[c.verdict]).verdict if cells else "stable"


# ---------------------------------------------------------------------------
# report
# ---------------------------------------------------------------------------
_HEADLINE_COLUMNS = [
    ("value", "value"),
    ("peak_force_mn", "peak F (MN)"),
    ("peak_torque_knm", "peak roll T (kN·m)"),
    ("peak_power_kw", "peak P (kW)"),
    ("gearbox_output_required_knm", "gearbox out req (kN·m)"),
    ("regen_kw", "regen (kW)"),
    ("accel_brake_per_h_lo", "accel/brake lo (/h)"),
    ("accel_brake_per_h_hi", "accel/brake hi (/h)"),
    ("capacity_tph_lo", "capacity lo (t/h)"),
    ("capacity_tph_hi", "capacity hi (t/h)"),
    ("finish_temp_12mm_c", "finish@12mm (C)"),
    ("finish_temp_6mm_c", "finish@6mm (C)"),
    ("bite_limit_mm", "bite limit (mm)"),
]


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.3g}"
    return str(v)


def render_headline_table(experiment: Experiment,
                          rows: list[tuple[object, HeadlineResult]]) -> str:
    header = [label for _, label in _HEADLINE_COLUMNS]
    lines = ["| " + " | ".join(header) + " |",
            "|" + "---|" * len(header)]
    for value, res in rows:
        cells = [value] + [getattr(res, key) for key, _ in _HEADLINE_COLUMNS[1:]]
        lines.append("| " + " | ".join(_fmt(c) for c in cells) + " |")
    return "\n".join(lines)


def render_ar3_table(rows: list[Ar3Row]) -> str:
    thicknesses = sorted(rows[0].finish_temps) if rows else []
    header = ["Ar3 threshold (C)"] + [f"{t:g} mm" for t in thicknesses] + ["thicknesses passing"]
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for row in rows:
        cells = [f"{row.threshold_c:g}"]
        for t in thicknesses:
            temp, ok = row.finish_temps[t]
            cells.append(f"{temp:.0f} C {'PASS' if ok else 'FAIL'}")
        cells.append(f"{row.n_pass}/{len(thicknesses)}")
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def render_fragility_matrix(all_cells: dict[str, list[FragilityCell]]) -> str:
    claim_ids = [c.id for c in txm.CLAIMS]
    exp_ids = [e.id for e in EXPERIMENTS]
    header = ["claim"] + exp_ids
    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    for claim_id in claim_ids:
        row = [claim_id]
        for exp_id in exp_ids:
            cells = [c for c in all_cells[exp_id] if c.claim_id == claim_id]
            row.append(worst_verdict(cells))
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def rank_inputs(all_cells: dict[str, list[FragilityCell]]) -> list[tuple[str, int, int]]:
    """(experiment_id, n_moves, n_breaks) sorted by 2*breaks + moves, desc."""
    scored = []
    for exp_id, cells in all_cells.items():
        n_moves = sum(1 for c in cells if c.verdict == "moves")
        n_breaks = sum(1 for c in cells if c.verdict == "breaks")
        scored.append((exp_id, n_moves, n_breaks))
    scored.sort(key=lambda r: (2 * r[2] + r[1]), reverse=True)
    return scored


def build_report(today: str | None = None) -> str:
    today = today or datetime.date.today().isoformat()
    parts = [
        "# Slab-Line What-If Sensitivity Report",
        "",
        f"Generated {today}. **This is sensitivity analysis on a concept model "
        "(`slab_line_design.py`) — not a set of operating setpoints, recipes, or "
        "trial instructions.** Every row below perturbs one UNSOURCED or "
        "literature-range engineering assumption (see "
        "`docs/system/MODEL_LITERATURE_VALIDATION_2026-09-26.md`) and recomputes "
        "the model; nothing here has been released, purchased, or sent to a vendor.",
        "",
    ]

    all_cells: dict[str, list[FragilityCell]] = {}
    ar3_rows: list[Ar3Row] | None = None

    for i, experiment in enumerate(EXPERIMENTS, start=1):
        parts.append(f"## {i}. `{experiment.id}` — {experiment.parameter}")
        parts.append("")
        parts.append(f"Values tested: {', '.join(_fmt(v) for v in experiment.values)}")
        parts.append("")
        parts.append(f"Basis: {experiment.basis_note}")
        parts.append("")
        parts.append(f"Reference: {experiment.literature_ref}")
        parts.append("")
        if experiment.id == "ar3-threshold":
            ar3_rows = run_ar3_experiment(experiment)
            parts.append(render_ar3_table(ar3_rows))
        else:
            rows = run_experiment_headline(experiment)
            parts.append(render_headline_table(experiment, rows))
        parts.append("")
        all_cells[experiment.id] = run_transmission_fragility(experiment)

    parts.append("## Fragility matrix — nexus_checks.transmission claims vs. experiments")
    parts.append("")
    parts.append("`stable`: rounded vendor-facing number unchanged. `moves`: rounded "
                 "value changes by less than 25%. `breaks`: rounded value changes by "
                 "25% or more, or recomputation fails outright. `CLAIMS_INPUT` entries "
                 "(no model function behind them) are not shown - there is nothing to "
                 "recompute for them.")
    parts.append("")
    parts.append("Note on `accel-torque-12-29`: its reported 12-29 kN·m bracket "
                 "already mixes two different (rotor inertia, ramp time) pairs - 450 "
                 "kg·m² @ 3 s for the low end, 750 kg·m² @ 2 s for "
                 "the high end. A single swept `rotor-inertia` or `ramp-time` value can "
                 "match at most one end of that bracket, never both, so this claim shows "
                 "`breaks` at every tested value of those two experiments by "
                 "construction - that is a property of the claim's own basis, not a "
                 "sign that the model itself is unstable.")
    parts.append("")
    parts.append(render_fragility_matrix(all_cells))
    parts.append("")

    parts.append("## Ranked: inputs that most move vendor-facing numbers")
    parts.append("")
    for rank, (exp_id, n_moves, n_breaks) in enumerate(rank_inputs(all_cells), start=1):
        parts.append(f"{rank}. `{exp_id}` — {n_breaks} claim(s) BREAK, {n_moves} claim(s) MOVE "
                     "across its tested values")
    parts.append("")

    return "\n".join(parts) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description="Read-only what-if experiment harness for slab_line_design.py. "
                   "Sensitivity analysis only - never prints or writes an operating "
                   "setpoint.")
    ap.add_argument("--report", help="write the markdown report to this path")
    args = ap.parse_args(argv)

    report = build_report()
    if args.report:
        out_path = Path(args.report)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report, encoding="utf-8")
        print(f"wrote {out_path}")
    else:
        print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
