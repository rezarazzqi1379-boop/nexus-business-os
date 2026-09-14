"""Tests for rolling_mill_mechanics.py.

These validate geometry/behavioral correctness (dimensional consistency, monotonicity,
fail-closed gating) rather than exact numeric agreement with any single textbook example
— per project discipline, this module does not assert an unverified numeric constant as
ground truth.
"""

import math

import pytest

from rolling_mill_intake import RollingReadiness
from rolling_mill_mechanics import (
    HistoricalPass,
    biting_condition_ok,
    bite_angle_rad,
    compare_power_with_motor_rating,
    contact_length_mm,
    draft_mm,
    estimate_pass_force,
    mean_strain_rate_per_s,
    reduction_ratio,
    run_retrospective_envelope,
    true_strain,
)


def test_draft_basic():
    assert draft_mm(20, 15) == 5
    assert draft_mm(20, 20) == 0


def test_draft_rejects_impossible_pass():
    with pytest.raises(ValueError):
        draft_mm(15, 20)


def test_reduction_ratio():
    assert reduction_ratio(20, 15) == pytest.approx(0.25)


def test_contact_length_zero_draft():
    assert contact_length_mm(225, 20, 20) == 0


def test_contact_length_matches_formula():
    r, h0, h1 = 225.0, 20.0, 15.0
    expected = math.sqrt(r * (h0 - h1))
    assert contact_length_mm(r, h0, h1) == pytest.approx(expected)


def test_contact_length_monotonic_in_draft():
    r, h0 = 225.0, 20.0
    l_small = contact_length_mm(r, h0, 18.0)
    l_large = contact_length_mm(r, h0, 12.0)
    assert l_large > l_small


def test_bite_angle_zero_when_no_draft():
    assert bite_angle_rad(225, 20, 20) == pytest.approx(0.0)


def test_bite_angle_matches_cosine_definition():
    r, h0, h1 = 225.0, 20.0, 15.0
    alpha = bite_angle_rad(r, h0, h1)
    assert math.cos(alpha) == pytest.approx(1.0 - (h0 - h1) / (2 * r))


def test_bite_angle_monotonic_in_draft():
    r, h0 = 225.0, 20.0
    a_small = bite_angle_rad(r, h0, 18.0)
    a_large = bite_angle_rad(r, h0, 12.0)
    assert a_large > a_small


def test_true_strain_positive_for_valid_pass():
    assert true_strain(20, 15) == pytest.approx(math.log(20 / 15))


def test_true_strain_rejects_nonpositive_thickness():
    with pytest.raises(ValueError):
        true_strain(0, 10)
    with pytest.raises(ValueError):
        true_strain(10, 0)


def test_mean_strain_rate_rejects_zero_speed():
    # A stopped mill isn't rolling; zero speed isn't a meaningful in-pass state.
    with pytest.raises(ValueError):
        mean_strain_rate_per_s(0.0, 225, 20, 15)


def test_mean_strain_rate_positive_for_valid_pass():
    rate = mean_strain_rate_per_s(500.0, 225, 20, 15)
    assert rate > 0


def test_biting_condition_boundary():
    # tan(alpha) == mu is the boundary; slightly above mu should fail.
    alpha = math.radians(10)
    mu = math.tan(alpha)
    assert biting_condition_ok(alpha, mu + 1e-9) is True
    assert biting_condition_ok(alpha, mu - 0.05) is False


def test_biting_condition_rejects_nonpositive_mu():
    with pytest.raises(ValueError):
        biting_condition_ok(0.1, 0)


def test_estimate_pass_force_without_material_model_leaves_force_none():
    result = estimate_pass_force(
        roll_radius_mm=225,
        entry_thickness_mm=20,
        exit_thickness_mm=15,
        strip_width_mm=300,
    )
    assert result.roll_force_n is None
    assert result.roll_torque_nm is None
    assert result.power_kw is None
    assert any("not computed" in note for note in result.notes)


def test_estimate_pass_force_with_material_model_produces_force():
    def toy_flow_stress(strain, strain_rate, temperature_degC):
        # Deliberately simple placeholder — this is a test fixture, not a claimed
        # calibrated material model for any real steel grade.
        return 100.0 + 5.0 * strain

    result = estimate_pass_force(
        roll_radius_mm=225,
        entry_thickness_mm=20,
        exit_thickness_mm=15,
        strip_width_mm=300,
        roll_surface_speed_mm_s=500.0,
        temperature_degC=1000.0,
        friction_coefficient=0.3,
        flow_stress_model=toy_flow_stress,
    )
    assert result.roll_force_n is not None
    assert result.roll_force_n > 0
    assert result.roll_torque_nm > 0
    assert result.power_kw > 0


def test_estimate_pass_force_flags_infeasible_bite():
    def toy_flow_stress(strain, strain_rate, temperature_degC):
        return 100.0

    # Large draft on a small roll radius with very low friction should fail biting.
    result = estimate_pass_force(
        roll_radius_mm=225,
        entry_thickness_mm=20,
        exit_thickness_mm=5,
        strip_width_mm=300,
        roll_surface_speed_mm_s=500.0,
        temperature_degC=1000.0,
        friction_coefficient=0.05,
        flow_stress_model=toy_flow_stress,
    )
    assert result.biting_feasible is False
    assert any("biting condition FAILS" in note for note in result.notes)


def test_run_retrospective_envelope_refuses_when_gate_closed():
    closed = RollingReadiness(
        status="READY_FOR_ENGINEER_INTERVIEW",
        missing_paths=("product.target.width_mm",),
        unresolved_claims=("claim_target_300",),
        calculation_allowed=False,
        operation_change_allowed=False,
        next_gate="answer questionnaire",
    )
    with pytest.raises(PermissionError):
        run_retrospective_envelope(closed, passes=[])


def test_run_retrospective_envelope_runs_when_gate_open():
    open_gate = RollingReadiness(
        status="READY_FOR_RETROSPECTIVE_CALCULATION",
        missing_paths=(),
        unresolved_claims=(),
        calculation_allowed=True,
        operation_change_allowed=False,
        next_gate="independent engineer review of measured historical pass data",
    )
    passes = [
        HistoricalPass(
            stand_id="stand_1",
            entry_thickness_mm=20,
            exit_thickness_mm=15,
            strip_width_mm=300,
            roll_radius_mm=225,
        )
    ]
    results = run_retrospective_envelope(open_gate, passes)
    assert len(results) == 1
    assert results[0].contact_length_mm > 0


def test_compare_power_with_motor_rating_flags_overload():
    result = compare_power_with_motor_rating(150.0, 125.0)
    assert result["exceeds_nameplate"] is True
    assert result["utilization_ratio"] == pytest.approx(1.2)


def test_compare_power_with_motor_rating_within_limit():
    result = compare_power_with_motor_rating(100.0, 125.0)
    assert result["exceeds_nameplate"] is False
