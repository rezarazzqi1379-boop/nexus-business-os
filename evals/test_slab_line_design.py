import math
import pytest
from slab_line_design import (
    SLAB_WIDTH_MM, SLAB_THICKNESS_MM, SLAB_LENGTH_MM, RHO, THICKNESS_TARGETS_MM,
    ROLL_DIAMETER_MM, BARREL_LENGTH_MM, MAX_LINE_SPEED_M_S, HOLD_POINTS, GRADES,
    mass_balance, product_length_m, max_draft_bite_mm, bite_angle_deg,
    contact_length_mm, roll_rpm, wusatowski_exit_width_mm, flow_stress_mpa,
    max_draft_bite_exact_mm,
    geometry_factor, constrained_factor, PLANE_STRAIN_FACTOR,
    neck_bending_stress_mpa, barrel_deflection_mm, lateral_margin_mm,
    cooling_rate_c_per_s, biot_number, build_schedule, worst_cases,
    cycle_summary, roller_table_requirement_m, torque_chain, total_service_factor,
    build_dc_option, dc_motor_feasibility, pinion_centre_distance_mm,
    spindle_angle_deg, gearbox_centre_distance_mm, STANDARD_RATIOS,
)


# --- mass balance: pure geometry, must close exactly --------------------------
def test_slab_mass_from_declared_dimensions():
    mb = mass_balance()
    assert mb.slab_volume_m3 == pytest.approx(0.15)
    assert mb.slab_mass_kg == pytest.approx(1177.5, abs=0.1)


def test_slabs_per_hour_and_cycle_are_consistent():
    mb = mass_balance()
    assert mb.slabs_per_hour * mb.slab_mass_kg / 1000.0 == pytest.approx(20.0)
    assert mb.slabs_per_hour * mb.cycle_time_s == pytest.approx(3600.0)


def test_product_length_conserves_volume_exactly():
    for t in THICKNESS_TARGETS_MM:
        L = product_length_m(t, yield_fraction=1.0)
        assert L * (t / 1000) * (SLAB_WIDTH_MM / 1000) == pytest.approx(0.15, rel=1e-12)


def test_product_length_is_inversely_proportional_to_thickness():
    assert product_length_m(6.0) / product_length_m(30.0) == pytest.approx(5.0, rel=1e-12)
    assert product_length_m(6.0) == pytest.approx(60.0, abs=0.1)


def test_product_length_rejects_nonsense():
    with pytest.raises(ValueError):
        product_length_m(0.0)


# --- bite ---------------------------------------------------------------------
def test_bite_limit_matches_the_stated_formula():
    assert max_draft_bite_mm(0.30) == pytest.approx(0.30 ** 2 * 300.0)
    assert max_draft_bite_mm(0.30) == pytest.approx(27.0)


def test_exact_bite_limit_satisfies_tan_alpha_equals_mu():
    """tan(alpha_max) = mu is the condition the draft limit comes from."""
    for mu in (0.25, 0.30, 0.35):
        a = bite_angle_deg(max_draft_bite_exact_mm(mu))
        assert math.tan(math.radians(a)) == pytest.approx(mu, rel=1e-9)


def test_classical_mu_squared_R_overstates_the_bite_limit():
    """dh = mu^2 R is a small-angle approximation and is optimistic. Pin the
    size of the optimism so a schedule is never built on it unknowingly."""
    for mu, max_over in ((0.25, 0.055), (0.30, 0.075), (0.35, 0.10)):
        over = max_draft_bite_mm(mu) / max_draft_bite_exact_mm(mu) - 1.0
        assert 0.0 < over < max_over


def test_contact_length_is_sqrt_R_times_draft():
    assert contact_length_mm(25.0) == pytest.approx(math.sqrt(300.0 * 25.0))


def test_roll_rpm_against_a_hand_value():
    assert roll_rpm(3.0) == pytest.approx(60 * 3.0 / (math.pi * 0.6))
    assert roll_rpm(3.0) == pytest.approx(95.49, abs=0.02)


def test_roll_rpm_scales_linearly_with_speed():
    assert roll_rpm(2.0) == pytest.approx(2 * roll_rpm(1.0))


# --- spread: the reason a slab beats a billet ---------------------------------
def test_spread_from_a_wide_slab_is_small():
    b = SLAB_WIDTH_MM
    for h0, h1 in ((125, 60), (60, 30), (30, 12), (12, 6)):
        b = wusatowski_exit_width_mm(h0, h1, b)
    assert 400.0 < b < 410.0, "a 400 mm slab should stay near 400 mm"


def test_spread_never_narrows_the_stock():
    assert wusatowski_exit_width_mm(125, 60, 400.0) >= 400.0


def test_spread_rejects_a_thickness_increase():
    with pytest.raises(ValueError):
        wusatowski_exit_width_mm(60, 125, 400.0)


# --- material -----------------------------------------------------------------
def test_flow_stress_matches_its_calibration_anchors():
    for T, expected in ((1200, 65), (1100, 88), (1000, 120), (900, 163)):
        assert flow_stress_mpa(T, 10.0, 0.3) == pytest.approx(expected, rel=0.03)


def test_flow_stress_falls_with_temperature_and_rises_with_rate():
    assert flow_stress_mpa(1200, 10, 0.3) < flow_stress_mpa(900, 10, 0.3)
    assert flow_stress_mpa(1100, 1, 0.3) < flow_stress_mpa(1100, 100, 0.3)


def test_s355_is_harder_than_s235_by_the_declared_multiplier():
    r = flow_stress_mpa(1100, 10, 0.3, "S355JR") / flow_stress_mpa(1100, 10, 0.3, "S235JR")
    assert r == pytest.approx(GRADES["S355JR"][0])


def test_unknown_grade_is_rejected_loudly():
    with pytest.raises(ValueError):
        flow_stress_mpa(1100, 10, 0.3, "S690QL")


def test_wide_stock_yields_in_plane_strain():
    """400 mm wide at 12 mm thick is b/h = 33 - firmly plane strain."""
    assert constrained_factor(400.0, 12.0) == pytest.approx(PLANE_STRAIN_FACTOR)
    assert constrained_factor(400.0, 12.0) == pytest.approx(1.1547, abs=1e-4)
    assert constrained_factor(100.0, 100.0) == pytest.approx(1.0)


def test_geometry_factor_switches_regime_at_L_over_h_of_one():
    assert geometry_factor(50.0, 100.0, 0.3) < 1.0      # thick stock
    assert geometry_factor(100.0, 50.0, 0.3) > 1.0      # friction hill


# --- DIMENSIONAL CHECKS: these are the ones that catch unit bugs ---------------
def test_bearing_torque_is_a_small_fraction_of_rolling_torque():
    """REGRESSION. The neck radius is in mm and the rolling torque is in N.m.
    A missing /1000 on the bearing term made the total torque ~20x too large
    and was only visible as an absurd power figure. Bearing loss on an oil-film
    neck should be a few percent of the rolling torque, never a multiple."""
    s = build_schedule(30.0, "balanced")
    for p in s:
        t_rolling_only = 2.0 * p.force_n * 0.48 * p.contact_len / 1000.0
        assert p.torque_roll_nm == pytest.approx(t_rolling_only, rel=0.10), (
            f"pass {p.index}: total torque {p.torque_roll_nm:.0f} N.m is not within "
            f"10% of the pure rolling torque {t_rolling_only:.0f} N.m")


def test_power_torque_speed_are_mutually_consistent():
    """P = T omega, checked in reverse for every pass."""
    for p in build_schedule(12.0, "balanced"):
        omega = 2 * math.pi * p.roll_rpm / 60.0
        assert p.power_kw == pytest.approx(p.torque_roll_nm * omega / 1000.0, rel=1e-9)


def test_force_stays_in_a_physically_sane_range():
    """A 400 mm wide pass on a 600 mm roll cannot plausibly need 50 MN."""
    for t in THICKNESS_TARGETS_MM:
        for p in build_schedule(t, "aggressive", grade="S355JR"):
            assert 0.1e6 < p.force_n < 20e6, f"{t} mm pass {p.index}: {p.force_n:.3e} N"


# --- roll mechanics -----------------------------------------------------------
def test_lateral_margin_is_100_mm_per_side():
    assert lateral_margin_mm() == pytest.approx((BARREL_LENGTH_MM - 400.0) / 2.0)
    assert lateral_margin_mm() == pytest.approx(100.0)


def test_this_stand_is_unusually_stiff():
    """D/L = 1.0. Deflection under the worst computed force stays far below the
    thickness tolerance of any candidate standard."""
    worst = max(max(p.force_n for p in build_schedule(t, "aggressive", grade="S355JR"))
                for t in THICKNESS_TARGETS_MM)
    assert barrel_deflection_mm(worst) < 0.2
    assert ROLL_DIAMETER_MM / BARREL_LENGTH_MM == pytest.approx(1.0)


def test_neck_stress_rises_linearly_with_force():
    assert neck_bending_stress_mpa(2e6) * 2 == pytest.approx(neck_bending_stress_mpa(4e6))


def test_deflection_falls_with_the_fourth_power_of_diameter():
    a = barrel_deflection_mm(3e6, diameter_mm=600.0)
    b = barrel_deflection_mm(3e6, diameter_mm=700.0)
    assert a / b == pytest.approx((700 / 600) ** 4, rel=1e-9)


# --- thermal ------------------------------------------------------------------
def test_thin_sections_cool_far_faster_than_the_slab():
    assert cooling_rate_c_per_s(6.0, 400.0, 1000.0) > 10 * cooling_rate_c_per_s(125.0, 400.0, 1000.0)


def test_slab_is_not_lumped_but_the_thin_product_is():
    assert biot_number(125.0, 400.0, 1250.0) > 0.1
    assert biot_number(8.0, 400.0, 950.0) < 0.1


# --- schedule -----------------------------------------------------------------
def test_schedule_reaches_the_target_and_respects_the_bite_limit():
    for t in THICKNESS_TARGETS_MM:
        for sc in ("conservative", "balanced", "aggressive"):
            s = build_schedule(t, sc)
            assert s[-1].exit_h == pytest.approx(t, abs=1e-6)
            assert all(p.bite_ok for p in s)


def test_thickness_chains_correctly_through_the_schedule():
    s = build_schedule(12.0, "balanced")
    for a, b in zip(s, s[1:]):
        assert b.entry_h == pytest.approx(a.exit_h)
        assert b.entry_b == pytest.approx(a.exit_b)


def test_aggressive_needs_fewer_passes_but_more_force():
    c = build_schedule(12.0, "conservative")
    a = build_schedule(12.0, "aggressive")
    assert len(a) < len(c)
    assert max(p.force_n for p in a) > max(p.force_n for p in c)


def test_temperature_falls_monotonically_through_the_schedule():
    s = build_schedule(12.0, "balanced")
    assert s[-1].exit_temp_c < s[0].entry_temp_c
    for a, b in zip(s, s[1:]):
        assert b.entry_temp_c <= a.exit_temp_c + 1e-9


def test_the_declared_3_m_s_is_a_ceiling_not_every_pass():
    s = build_schedule(12.0, "balanced")
    assert s[0].speed_m_s < MAX_LINE_SPEED_M_S
    assert max(p.speed_m_s for p in s) == pytest.approx(MAX_LINE_SPEED_M_S)


def test_worst_case_is_not_one_single_pass():
    """The instruction that motivated this: the worst pass for force, torque,
    power, length and temperature are different passes."""
    w = worst_cases(build_schedule(12.0, "balanced"))
    assert len({w["max_force"].index, w["max_torque"].index, w["max_power"].index}) > 1


def test_schedule_rejects_an_impossible_target():
    with pytest.raises(ValueError):
        build_schedule(200.0, "balanced")
    with pytest.raises(ValueError):
        build_schedule(12.0, "reckless")


# --- capacity and layout ------------------------------------------------------
def test_roller_table_requirement_grows_as_the_product_thins():
    thin = roller_table_requirement_m(build_schedule(6.0, "balanced"))
    thick = roller_table_requirement_m(build_schedule(30.0, "balanced"))
    assert thin["table_each_side_m"] > 4 * thick["table_each_side_m"]
    assert thin["table_each_side_m"] > 60.0


def test_capacity_falls_as_the_product_thins():
    assert cycle_summary(build_schedule(6.0, "balanced"))["tph"] < \
           cycle_summary(build_schedule(30.0, "balanced"))["tph"]


# --- drive --------------------------------------------------------------------
def test_service_factor_is_a_product_of_named_terms():
    assert total_service_factor() == pytest.approx(1.75 * 1.15 * 1.00 * 1.10)
    assert total_service_factor() > 2.0


def test_gearbox_rating_is_never_the_mean_torque():
    s = build_schedule(30.0, "balanced")
    ch = torque_chain(s, 12.5, cycle_summary(s)["cycle_s"])
    assert ch.gearbox_output_required_nm > ch.continuous_roll_nm
    assert ch.rms_roll_nm < ch.peak_rolling_roll_nm


def test_motor_shaft_torque_falls_as_the_ratio_rises():
    s = build_schedule(30.0, "balanced")
    c = cycle_summary(s)["cycle_s"]
    assert torque_chain(s, 14.0, c).motor_shaft_nm < torque_chain(s, 8.0, c).motor_shaft_nm


def test_dc_option_always_reaches_the_declared_line_speed():
    """The ratio must snap DOWN. Snapping up puts 3 m/s out of reach."""
    s = build_schedule(12.0, "balanced")
    for kw, base, fw in ((1250, 450, 2.5), (1600, 400, 3.0), (2000, 350, 3.0)):
        o = build_dc_option("x", s, kw, base, fw, "test")
        assert o.max_roll_speed_m_s >= MAX_LINE_SPEED_M_S
        assert o.gear_ratio in STANDARD_RATIOS


def test_dc_characteristic_is_constant_torque_then_constant_power():
    """The defining DC behaviour this whole selection rests on: below base speed
    torque is flat, above it power is flat (so torque falls as 1/n)."""
    kw, base = 1600.0, 400.0
    w_base = 2 * math.pi * base / 60.0
    t_base = kw * 1000.0 / w_base
    def avail(n):
        return t_base if n <= base else t_base * base / n
    assert avail(200) == pytest.approx(avail(400))                 # flat below base
    assert avail(800) == pytest.approx(t_base / 2.0)               # halves at 2x base
    for n in (500, 800, 1200):                                     # constant power aloft
        assert avail(n) * 2 * math.pi * n / 60.0 == pytest.approx(kw * 1000.0)


def test_a_lower_base_speed_buys_torque_only_below_base():
    """Dropping base speed at fixed kW raises base torque, but gives nothing at
    the top of the range, where power is the limit."""
    s = build_schedule(30.0, "balanced")
    _, m_400, _ = dc_motor_feasibility(s, 1600.0, 400.0, 3.0, 12.5)
    _, m_200, _ = dc_motor_feasibility(s, 1600.0, 200.0, 6.0, 12.5)
    assert m_200 >= m_400


def test_a_motor_that_cannot_reach_the_speed_is_reported_infeasible():
    s = build_schedule(12.0, "balanced")
    ok, margin, _ = dc_motor_feasibility(s, 1600.0, 100.0, 1.0, 12.5)
    assert not ok and margin == -100.0


def test_no_standard_ratio_raises_rather_than_silently_underspeeding():
    with pytest.raises(ValueError):
        build_dc_option("x", build_schedule(12.0, "balanced"), 1600.0, 100.0, 1.0, "test")


# --- the "senter" question ----------------------------------------------------
def test_pinion_centres_track_roll_centres():
    assert pinion_centre_distance_mm(12.0) == pytest.approx(612.0)
    assert pinion_centre_distance_mm(0.0) == pytest.approx(ROLL_DIAMETER_MM)


def test_spindle_angle_stays_small_across_the_gap_and_wear_range():
    for centres in (606.0, 630.0, 572.0):
        assert spindle_angle_deg(618.0, centres, 1500.0) < 2.0


def test_gearbox_centre_distance_follows_the_gear_formula():
    assert gearbox_centre_distance_mm(5.0, 14.0, 22) == pytest.approx(14.0 * (22 + 110) / 2)


# --- discipline ---------------------------------------------------------------
def test_hold_points_are_declared():
    joined = " ".join(HOLD_POINTS)
    for must in ("bearing", "housing", "reversing", "grade", "bay length"):
        assert must in joined
