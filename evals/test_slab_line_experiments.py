"""Tests for slab_line_experiments.py, the read-only what-if harness.

(a) constants are exactly restored after every experiment, including when an
    exception is raised mid-perturbation;
(b) at nominal values the harness reproduces slab_line_design's current
    outputs exactly, and every model-sourced transmission claim reads
    "stable" at its own nominal value;
(c) monotonic sanity: force rises with mu and with the flow-stress scale;
    regen rises with inertia and falls with ramp time;
(d) the Ar3 classification is consistent: a higher threshold never passes
    more thicknesses;
(e) running the full transmission check afterwards still passes - proof that
    nothing leaked out of any experiment.
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest

import slab_line_design as sld
import slab_line_experiments as exp
from nexus_checks import transmission as txm

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs" / "procurement"

# Captured once, before any test in this module perturbs anything, so every
# "did it come back?" assertion has a fixed point of comparison.
_ORIGINAL_SCENARIOS = copy.deepcopy(sld.SCENARIOS)
_ORIGINAL_FS_A = sld.FS_A
_ORIGINAL_GRADES = copy.deepcopy(sld.GRADES)

NOMINAL_VALUE = {
    "friction-mu": 0.30,
    "flow-stress-scale": 1.00,
    "grade": "S355JR",
    "rotor-inertia": 750.0,
    "ramp-time": 3.0,
}


def _experiment(id_: str) -> exp.Experiment:
    return next(e for e in exp.EXPERIMENTS if e.id == id_)


def _run_any(experiment: exp.Experiment):
    if experiment.id == "ar3-threshold":
        return exp.run_ar3_experiment(experiment)
    return exp.run_experiment_headline(experiment)


# ---- (a) restoration, always -------------------------------------------------
def test_a_override_constants_restores_after_an_exception():
    original = sld.MU_BEARING
    with pytest.raises(RuntimeError):
        with exp.override_constants(sld, MU_BEARING=999.0):
            assert sld.MU_BEARING == 999.0
            raise RuntimeError("boom")
    assert sld.MU_BEARING == original


def test_a_override_constants_restores_a_previously_absent_attribute():
    assert not hasattr(sld, "_EXPERIMENT_PROBE_ATTR")
    with exp.override_constants(sld, _EXPERIMENT_PROBE_ATTR=1):
        assert sld._EXPERIMENT_PROBE_ATTR == 1
    assert not hasattr(sld, "_EXPERIMENT_PROBE_ATTR")


def test_a_nested_overrides_unwind_in_order():
    base = sld.FS_A
    with exp.override_constants(sld, FS_A=base * 2):
        assert sld.FS_A == base * 2
        with exp.override_constants(sld, FS_A=base * 3):
            assert sld.FS_A == base * 3
        assert sld.FS_A == base * 2
    assert sld.FS_A == base


@pytest.mark.parametrize("experiment", exp.EXPERIMENTS, ids=lambda e: e.id)
def test_a_every_experiment_restores_module_state(experiment):
    _run_any(experiment)
    exp.run_transmission_fragility(experiment)
    assert sld.SCENARIOS == _ORIGINAL_SCENARIOS
    assert sld.FS_A == _ORIGINAL_FS_A
    assert sld.GRADES == _ORIGINAL_GRADES


# ---- (b) nominal reproduces the model exactly --------------------------------
def test_b_nominal_headline_matches_direct_model_calls():
    truth = exp.compute_headline(sld, exp.RunConfig())

    rows = dict(exp.run_experiment_headline(_experiment("friction-mu")))
    at_nominal = rows[0.30]
    assert at_nominal.peak_force_mn == pytest.approx(truth.peak_force_mn, rel=1e-9)
    assert at_nominal.peak_torque_knm == pytest.approx(truth.peak_torque_knm, rel=1e-9)
    assert at_nominal.bite_limit_mm == pytest.approx(truth.bite_limit_mm, rel=1e-9)

    rows = dict(exp.run_experiment_headline(_experiment("flow-stress-scale")))
    assert rows[1.00].peak_force_mn == pytest.approx(truth.peak_force_mn, rel=1e-9)

    rows = dict(exp.run_experiment_headline(_experiment("grade")))
    assert rows["S355JR"].peak_force_mn == pytest.approx(truth.peak_force_mn, rel=1e-9)

    rows = dict(exp.run_experiment_headline(_experiment("rotor-inertia")))
    assert rows[750.0].regen_kw == pytest.approx(truth.regen_kw, rel=1e-9)

    rows = dict(exp.run_experiment_headline(_experiment("ramp-time")))
    assert rows[3.0].regen_kw == pytest.approx(truth.regen_kw, rel=1e-9)


def test_b_fragility_is_stable_at_every_experiments_own_nominal_value():
    # accel-torque-12-29's own reported bracket already mixes TWO different
    # (motor_rotor_j, accel_time_s) pairs for its low/high end (450 kg.m^2 @
    # 3 s and 750 kg.m^2 @ 2 s - see nexus_checks/transmission.py
    # compute_accel_torque_range). A single swept rotor-inertia or ramp-time
    # value can reproduce at most one end of that mixed bracket, never both
    # at once, so it never reads "stable" here - that is a correct fragility
    # finding about the claim's own basis, not a harness defect. It is
    # excluded from this "reproduces nominal exactly" check for that reason.
    always_reproducible = {c.id for c in txm.CLAIMS} - {"accel-torque-12-29"}
    for exp_id, nominal_value in NOMINAL_VALUE.items():
        cells = [c for c in exp.run_transmission_fragility(_experiment(exp_id))
                if c.value == nominal_value and c.claim_id in always_reproducible]
        bad = [c for c in cells if c.verdict != "stable"]
        assert bad == [], f"{exp_id}: {bad}"
        assert cells, f"{exp_id}: no claims checked"


# ---- (c) monotonic sanity -----------------------------------------------------
def test_c_peak_force_rises_with_mu():
    rows = exp.run_experiment_headline(_experiment("friction-mu"))
    forces = [r.peak_force_mn for _, r in rows]
    assert forces == sorted(forces)
    assert forces[-1] > forces[0]


def test_c_bite_limit_rises_with_mu():
    rows = exp.run_experiment_headline(_experiment("friction-mu"))
    bites = [r.bite_limit_mm for _, r in rows]
    assert bites == sorted(bites)
    assert bites[-1] > bites[0]


def test_c_peak_force_rises_with_flow_stress_scale():
    rows = exp.run_experiment_headline(_experiment("flow-stress-scale"))
    forces = [r.peak_force_mn for _, r in rows]
    assert forces == sorted(forces)
    assert forces[-1] > forces[0]


def test_c_regen_rises_with_rotor_inertia():
    rows = exp.run_experiment_headline(_experiment("rotor-inertia"))
    regens = [r.regen_kw for _, r in rows]
    assert regens == sorted(regens)
    assert regens[-1] > regens[0]


def test_c_regen_falls_with_ramp_time():
    rows = exp.run_experiment_headline(_experiment("ramp-time"))
    regens = [r.regen_kw for _, r in rows]
    assert regens == sorted(regens, reverse=True)
    assert regens[0] > regens[-1]


# ---- (d) Ar3 classification is consistent -------------------------------------
def test_d_higher_ar3_threshold_never_passes_more_thicknesses():
    rows = exp.run_ar3_experiment(_experiment("ar3-threshold"))
    rows_by_threshold = sorted(rows, key=lambda r: r.threshold_c)
    for lower, higher in zip(rows_by_threshold, rows_by_threshold[1:]):
        assert higher.n_pass <= lower.n_pass


def test_d_ar3_pass_flag_matches_the_finish_temperature():
    rows = exp.run_ar3_experiment(_experiment("ar3-threshold"))
    for row in rows:
        for thickness, (temp, passed) in row.finish_temps.items():
            assert passed == (temp > row.threshold_c)


# ---- (e) no leaked state -------------------------------------------------------
def test_e_transmission_check_passes_after_every_experiment_has_run():
    for experiment in exp.EXPERIMENTS:
        _run_any(experiment)
        exp.run_transmission_fragility(experiment)

    findings = txm.check(sld, DOCS)
    errors = [f for f in findings if f.severity == "ERROR"]
    assert errors == [], "\n".join(f.fmt() for f in errors)


def test_e_full_report_builds_and_leaves_the_model_clean():
    report = exp.build_report(today="2026-09-28")
    assert report.startswith("# Slab-Line What-If Sensitivity Report")
    assert "sensitivity analysis on a concept model" in report
    assert "operating setpoint" in report or "not a set of operating setpoints" in report

    assert sld.SCENARIOS == _ORIGINAL_SCENARIOS
    assert sld.FS_A == _ORIGINAL_FS_A
    assert sld.GRADES == _ORIGINAL_GRADES

    findings = txm.check(sld, DOCS)
    assert [f for f in findings if f.severity == "ERROR"] == []


# ---- fragility matrix shape ----------------------------------------------------
def test_fragility_only_covers_model_sourced_claims():
    model_claim_ids = {c.id for c in txm.CLAIMS}
    input_claim_ids = {c.id for c in txm.CLAIMS_INPUT}
    cells = exp.run_transmission_fragility(_experiment("friction-mu"))
    seen = {c.claim_id for c in cells}
    assert seen == model_claim_ids
    assert seen.isdisjoint(input_claim_ids)
