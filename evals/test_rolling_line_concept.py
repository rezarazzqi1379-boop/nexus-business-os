import math
import pytest
from rolling_line_concept import (
    BASE, CONSERVATIVE, OPTIMISTIC, SCENARIO_A, SCENARIO_B, Billet, Stand,
    analyse_pass, build_concept_pass_schedule, contact_length_mm, flow_stress_mpa,
    geometry_factor, mass_flow_thickness_chain, max_draft_for_bite_mm,
    roll_barrel_deflection_mm, roll_neck_bending_stress_mpa, wusatowski_spread,
)

def test_billet_mass_matches_hand_calculation():
    b = Billet()
    assert b.area_mm2 == 22500
    assert b.mass_kg == pytest.approx(556.37, abs=0.1)

def test_flow_stress_calibration_anchors():
    # calibrated against published hot-working data for 0.15-0.20%C steel at 10/s
    assert flow_stress_mpa(1200, 10, 0.3) == pytest.approx(65, abs=6)
    assert flow_stress_mpa(1100, 10, 0.3) == pytest.approx(88, abs=8)
    assert flow_stress_mpa(1000, 10, 0.3) == pytest.approx(120, abs=10)
    assert flow_stress_mpa(900, 10, 0.3) == pytest.approx(163, abs=14)

def test_flow_stress_rises_as_temperature_falls():
    assert flow_stress_mpa(900, 5) > flow_stress_mpa(1100, 5) > flow_stress_mpa(1200, 5)

def test_flow_stress_rises_with_strain_rate():
    assert flow_stress_mpa(1100, 50) > flow_stress_mpa(1100, 5)

def test_flow_stress_rejects_nonphysical_input():
    for bad in ((0, 5, 0.3), (1100, 0, 0.3), (1100, 5, 0)):
        with pytest.raises(ValueError):
            flow_stress_mpa(*bad)

def test_bite_limit_is_mu_squared_times_radius():
    assert max_draft_for_bite_mm(0.30, 259) == pytest.approx(23.31, abs=0.01)
    # a rougher roll bites deeper
    assert max_draft_for_bite_mm(0.35, 259) > max_draft_for_bite_mm(0.25, 259)

def test_contact_length_matches_formula():
    assert contact_length_mm(259, 30) == pytest.approx(math.sqrt(259 * 30))

def test_spread_is_positive_but_modest_on_a_square_billet():
    out = wusatowski_spread(150, 120, 150, 518)
    assert 150 < out < 165  # natural spread is slow - this is the core finding

def test_spread_collapses_once_stock_is_wide_and_thin():
    # a wide thin strip barely spreads at all: width is locked in early
    narrow = wusatowski_spread(150, 120, 150, 518) - 150
    wide = wusatowski_spread(25, 20, 250, 600) - 250
    assert wide < narrow / 10

def test_spread_rejects_thickness_increase():
    with pytest.raises(ValueError):
        wusatowski_spread(100, 120, 150, 518)

def test_geometry_factor_regimes():
    thick = geometry_factor(50, 100, 0.3)   # L/h = 0.5, thick-stock regime
    thin = geometry_factor(50, 25, 0.3)     # L/h = 2.0, friction-hill regime
    assert thick < 1.0 < thin

def test_pass_analysis_produces_physical_values():
    p = analyse_pass(1, 150, 120, 150, SCENARIO_A, BASE, 165.8, 1150)
    assert p.force_n > 0 and p.torque_nm > 0 and p.power_kw > 0
    assert p.exit_b > p.entry_b
    assert 0 < p.bite_angle_deg < 45

def test_pass_rejects_non_reducing_pass():
    with pytest.raises(ValueError):
        analyse_pass(1, 120, 120, 150, SCENARIO_A, BASE, 165.8, 1150)

def test_concept_schedule_reaches_target_and_respects_bite_limit():
    passes = build_concept_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, 165.8)
    assert passes[-1].exit_h == pytest.approx(25.0, abs=0.01)
    assert all(p.bite_ok for p in passes), "concept schedule must never exceed the bite limit"

def test_larger_roll_permits_fewer_passes():
    a = build_concept_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, 165.8)
    b = build_concept_pass_schedule(Billet(), 25.0, SCENARIO_B, BASE, 176.1)
    assert len(b) <= len(a)  # bigger radius -> bigger permissible draft

def test_rougher_rolls_permit_fewer_passes():
    cons = build_concept_pass_schedule(Billet(), 25.0, SCENARIO_A, CONSERVATIVE, 165.8)
    opt = build_concept_pass_schedule(Billet(), 25.0, SCENARIO_A, OPTIMISTIC, 165.8)
    assert len(opt) < len(cons)

def test_neck_stress_scales_with_force_and_falls_with_diameter():
    s1 = roll_neck_bending_stress_mpa(1_500_000, 260)
    s2 = roll_neck_bending_stress_mpa(3_000_000, 260)
    s3 = roll_neck_bending_stress_mpa(1_500_000, 320)
    assert s2 == pytest.approx(2 * s1)
    assert s3 < s1

def test_neck_stress_rejects_bad_geometry():
    with pytest.raises(ValueError):
        roll_neck_bending_stress_mpa(1_000_000, 0)

def test_deflection_grows_with_force_and_shrinks_with_diameter():
    d_small_roll = roll_barrel_deflection_mm(1_500_000, SCENARIO_A, 300)
    d_big_roll = roll_barrel_deflection_mm(1_500_000, SCENARIO_B, 300)
    assert d_big_roll < d_small_roll
    assert roll_barrel_deflection_mm(3_000_000, SCENARIO_A, 300) > d_small_roll

def test_mass_flow_chain_requires_downstream_stands_to_be_thinner():
    stands = (
        Stand("ST1", 1250, 999, 9.8, 518),
        Stand("ST3", None, 1000, 8.6, 600),
        Stand("ST4", None, 1000, 5.6, 600),
    )
    chain = mass_flow_thickness_chain(stands, 8.0, 300.0)
    assert chain["ST1"] > chain["ST3"] > chain["ST4"]
    assert chain["ST4"] == pytest.approx(8.0)

def test_mass_flow_chain_fails_closed_without_speeds():
    with pytest.raises(ValueError):
        mass_flow_thickness_chain((Stand("X", None, None, 9.8, 518),), 8.0, 300.0)

def test_stand_kinematics_match_nameplate():
    st1 = Stand("ST1", 1250, 999, 9.8, 518)
    assert st1.roll_rpm == pytest.approx(999 / 9.8)
    assert st1.surface_speed_m_min == pytest.approx(math.pi * 0.518 * 999 / 9.8)
    assert st1.rated_motor_torque_nm == pytest.approx(11947, abs=50)
    assert st1.rated_roll_torque_nm(0.96) == pytest.approx(112396, abs=500)


# ---------------------------------------------------------------------------
# Grade-dependent behaviour
# ---------------------------------------------------------------------------

from rolling_line_concept import (
    A283C, CK45, GRADES, ST37, ST52, Grade,
    analyse_pass_for_grade, build_grade_pass_schedule, deformation_energy_kwh_per_tonne,
)

def _st1():
    return Stand("ST1", 1250, 999, 9.8, 518)

def _speed():
    return math.pi * 0.518 * (999 / 9.8)

def test_st37_is_the_unit_baseline():
    assert ST37.flow_stress_multiplier == 1.0

def test_grades_are_ordered_by_hot_strength():
    assert ST37.flow_stress_multiplier < A283C.flow_stress_multiplier
    assert A283C.flow_stress_multiplier < ST52.flow_stress_multiplier
    assert ST52.flow_stress_multiplier < CK45.flow_stress_multiplier

def test_every_grade_documents_its_basis():
    assert all(g.basis.strip() for g in GRADES)

def test_grade_scales_force_and_power_but_not_geometry():
    plain = analyse_pass(1, 150, 130, 150, SCENARIO_A, BASE, _speed(), 1150)
    alloy = analyse_pass_for_grade(1, 150, 130, 150, SCENARIO_A, BASE, _speed(), 1150, ST52)
    assert alloy.force_n == pytest.approx(plain.force_n * ST52.flow_stress_multiplier)
    assert alloy.power_kw == pytest.approx(plain.power_kw * ST52.flow_stress_multiplier)
    # geometry is unchanged by chemistry
    assert alloy.contact_len == pytest.approx(plain.contact_len)
    assert alloy.bite_angle_deg == pytest.approx(plain.bite_angle_deg)
    assert alloy.exit_b == pytest.approx(plain.exit_b)

def test_grade_schedule_never_exceeds_the_drive_limit():
    tq = _st1().rated_roll_torque_nm(BASE.gearbox_efficiency)
    for grade in GRADES:
        ps, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, grade)
        assert ps, f"{grade.name} produced no feasible schedule"
        assert all(p.power_kw <= 1250.0 + 1e-6 for p in ps), f"{grade.name} exceeded motor power"
        assert all(p.torque_nm <= tq + 1e-6 for p in ps), f"{grade.name} exceeded drive torque"

def test_harder_grade_needs_at_least_as_many_passes():
    tq = _st1().rated_roll_torque_nm(BASE.gearbox_efficiency)
    soft, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST37)
    hard, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, CK45)
    assert len(hard) >= len(soft)

def test_thick_product_needs_fewer_passes_than_thin():
    """The core spec-driven finding: thick gauge is cheaper to make, and that is
    exactly where the ST52 price premium sits."""
    tq = _st1().rated_roll_torque_nm(BASE.gearbox_efficiency)
    thin, _ = build_grade_pass_schedule(Billet(), 8.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST52)
    thick, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST52)
    assert len(thick) < len(thin)

def test_thin_product_costs_far_more_energy_per_tonne():
    tq = _st1().rated_roll_torque_nm(BASE.gearbox_efficiency)
    thin, _ = build_grade_pass_schedule(Billet(), 8.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST37)
    thick, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST37)
    e_thin = deformation_energy_kwh_per_tonne(thin)
    e_thick = deformation_energy_kwh_per_tonne(thick)
    assert e_thin > 1.7 * e_thick

def test_st52_at_25mm_costs_almost_no_capacity_versus_st37():
    """ST52 at thick gauge fits inside the existing drive envelope - the whole
    basis of the specification-driven recommendation."""
    tq = _st1().rated_roll_torque_nm(BASE.gearbox_efficiency)
    a, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST37)
    b, _ = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(), 1250.0, tq, ST52)
    assert len(b) == len(a)

def test_a_grade_too_hard_to_roll_fails_closed_rather_than_looping():
    tq = _st1().rated_roll_torque_nm(BASE.gearbox_efficiency)
    absurd = Grade("unrollable", 12.0, 0.9, 2.0, "deliberately beyond the drive envelope")
    ps, reasons = build_grade_pass_schedule(Billet(), 25.0, SCENARIO_A, BASE, _speed(),
                                            1250.0, tq, absurd, max_passes=15)
    assert "STALLED" in reasons or len(ps) <= 15
