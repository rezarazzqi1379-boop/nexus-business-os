import math
import pytest
from drive_train_sizing import (
    Product, build_schedule, build_drive_limited_schedule, roll_rpm, worn_diameter,
    gear_options, torque_chain, motor_sizing, electrical_consistency,
    synchronous_speed_rpm, mass_flow_speed_schedule, available_roll_torque_nm,
    capacity_limited_speed, thermal_limited_speed, mechanical_speed_ceiling,
    process_speed_ceiling, temperature_at_fraction, width_at_fraction,
    inertia_referred_to_motor, SERVICE_FACTORS, STANDARD_RATIOS, RELEASE_BLOCKERS,
)
from thermal_and_route_model import billet_section

LIMIT = available_roll_torque_nm(1250.0, 999.0, 9.8)
V = billet_section().volume_m3


# --- kinematics -------------------------------------------------------------
def test_roll_rpm_matches_the_stated_formula():
    """n = 60 v / (pi D). Checked against a hand value, not against itself."""
    assert roll_rpm(2.0, 518.0) == pytest.approx(60 * 2.0 / (math.pi * 0.518))
    assert roll_rpm(2.0, 518.0) == pytest.approx(73.73, abs=0.02)


def test_larger_diameter_needs_lower_rpm_for_the_same_linear_speed():
    assert roll_rpm(2.0, 700.0) < roll_rpm(2.0, 518.0)
    assert roll_rpm(2.0, 700.0) * 700.0 == pytest.approx(roll_rpm(2.0, 518.0) * 518.0)


def test_roll_wear_lowers_surface_speed_at_fixed_rpm():
    new, worn = 518.0, worn_diameter(518.0)
    assert worn < new
    v_new = math.pi * new / 1000 * 100 / 60
    v_worn = math.pi * worn / 1000 * 100 / 60
    assert v_worn / v_new == pytest.approx(worn / new)


def test_rpm_rejects_zero_diameter():
    with pytest.raises(ValueError):
        roll_rpm(1.0, 0.0)


# --- schedule ---------------------------------------------------------------
def test_schedule_reaches_the_target_thickness():
    s = build_schedule(Product(300, 25), 518.0, 2.0)
    assert s[-1].exit_h == pytest.approx(25.0, abs=1e-6)
    assert all(p.bite_ok for p in s)


def test_every_pass_reduces_thickness_and_chains_correctly():
    s = build_schedule(Product(300, 12), 518.0, 2.0)
    for a, b in zip(s, s[1:]):
        assert b.entry_h == pytest.approx(a.exit_h)
        assert b.exit_h < b.entry_h


def test_drive_limit_caps_torque_and_costs_passes():
    """The load-bearing behaviour: a torque ceiling buys itself in pass count."""
    free = build_schedule(Product(300, 25), 518.0, 2.0)
    limited = build_drive_limited_schedule(Product(300, 25), 518.0, 2.0, LIMIT)
    assert max(p.torque_drive_nm for p in free) > LIMIT
    assert max(p.torque_drive_nm for p in limited) <= LIMIT * 1.001
    assert len(limited) >= len(free)


def test_larger_diameter_allows_a_deeper_bite():
    small = build_schedule(Product(300, 25), 500.0, 2.0)
    large = build_schedule(Product(300, 25), 700.0, 2.0)
    assert max(p.draft for p in large) > max(p.draft for p in small)


def test_piece_length_grows_through_the_schedule():
    s = build_schedule(Product(300, 8), 518.0, 2.0)
    assert s[-1].piece_length_m > s[0].piece_length_m
    assert s[-1].piece_length_m == pytest.approx(29.5, abs=0.3)


def test_temperature_ramp_follows_the_declared_profile():
    assert temperature_at_fraction(0.0) == pytest.approx(1200.0)
    assert temperature_at_fraction(0.5) == pytest.approx(1050.0)
    assert temperature_at_fraction(1.0) == pytest.approx(800.0)
    assert 950.0 < temperature_at_fraction(0.7) < 1050.0


def test_width_ramp_is_monotone_and_lands_on_target():
    b = [width_at_fraction(f / 20, 150.0, 400.0) for f in range(21)]
    assert b == sorted(b)
    assert b[-1] == pytest.approx(400.0)


# --- speed envelope ---------------------------------------------------------
def test_capacity_speed_falls_when_handling_time_is_reduced():
    kw = dict(product=Product(300, 25), n_passes=8, piece_mass_kg=556.4,
              target_t_per_h=20.0, mean_piece_len_m=6.0)
    assert capacity_limited_speed(handling_s_per_pass=12.0, **kw) > \
           capacity_limited_speed(handling_s_per_pass=6.0, **kw)


def test_capacity_speed_is_infinite_when_handling_alone_blows_the_budget():
    v = capacity_limited_speed(Product(300, 8), 40, 556.4, 20.0, 30.0, 20.0)
    assert v == float("inf")


def test_thin_product_has_a_far_shorter_thermal_budget_than_thick():
    thin = build_drive_limited_schedule(Product(300, 8), 518.0, 3.0, LIMIT)
    thick = build_drive_limited_schedule(Product(300, 30), 518.0, 3.0, LIMIT)
    _, b_thin = thermal_limited_speed(Product(300, 8), thin, 950.0, 800.0, 6.0, V)
    _, b_thick = thermal_limited_speed(Product(300, 30), thick, 950.0, 800.0, 6.0, V)
    assert b_thick > 3 * b_thin


def test_mechanical_ceiling_takes_the_lower_of_peripheral_and_drive_limit():
    v = mechanical_speed_ceiling(518.0, "roughing", 1000.0, 9.8)
    assert v == pytest.approx(min(4.0, math.pi * 0.518 * (1000.0 / 9.8) / 60.0))


def test_process_ceiling_tightens_for_long_slender_bars():
    short, _ = process_speed_ceiling(Product(300, 30), 7.9)
    mid, _ = process_speed_ceiling(Product(300, 12), 19.7)
    assert mid < short


def test_a_piece_longer_than_the_bay_cannot_reverse_at_all():
    """The hard geometric result: 300x8 mm is 29.5 m long and the bay is 21 m."""
    v, why = process_speed_ceiling(Product(300, 8), 29.5, bay_length_m=21.0)
    assert v == 0.0
    assert "IMPOSSIBLE" in why


# --- gearbox ----------------------------------------------------------------
def test_gear_options_snap_onto_manufacturable_ratios():
    opts = gear_options(999.0, 1250.0, 75.0, 518.0)
    assert len(opts) == 3
    assert all(o.standard_ratio in STANDARD_RATIOS for o in opts)


def test_torque_biased_ratio_gives_more_torque_and_less_speed():
    t, b, s = gear_options(999.0, 1250.0, 75.0, 518.0)
    assert t.output_torque_capacity_nm > s.output_torque_capacity_nm
    assert t.linear_speed_m_s < s.linear_speed_m_s


def test_service_factor_is_a_product_of_named_terms_not_one_opaque_number():
    total = 1.0
    for v, _ in SERVICE_FACTORS.values():
        total *= v
    assert total > 1.5
    chain = torque_chain(build_drive_limited_schedule(Product(300, 25), 518.0, 2.0, LIMIT),
                         9.8, 60.0, 518.0, 1280.0)
    assert chain.service_factor_total == pytest.approx(total)


def test_rms_torque_is_below_peak_and_above_zero():
    s = build_drive_limited_schedule(Product(300, 25), 518.0, 2.0, LIMIT)
    c = torque_chain(s, 9.8, 60.0, 518.0, 1280.0)
    assert 0 < c.rms_nm < c.peak_rolling_nm


def test_rms_falls_as_idle_time_grows():
    s = build_drive_limited_schedule(Product(300, 25), 518.0, 2.0, LIMIT)
    busy = torque_chain(s, 9.8, 40.0, 518.0, 1280.0)
    slack = torque_chain(s, 9.8, 200.0, 518.0, 1280.0)
    assert slack.rms_nm < busy.rms_nm


def test_gearbox_rating_is_never_the_mean_torque():
    """The explicit instruction: do not set the gearbox rating equal to the
    average torque."""
    s = build_drive_limited_schedule(Product(300, 25), 518.0, 2.0, LIMIT)
    c = torque_chain(s, 9.8, 60.0, 518.0, 1280.0)
    assert c.gearbox_output_required_nm > c.continuous_nm


def test_inertia_referred_to_motor_falls_with_the_square_of_the_ratio():
    a = inertia_referred_to_motor(518.0, 1280.0, 2, 9.8, motor_rotor_j=0.0)
    b = inertia_referred_to_motor(518.0, 1280.0, 2, 19.6, motor_rotor_j=0.0)
    assert a / b == pytest.approx(4.0)


# --- motor ------------------------------------------------------------------
def test_motor_rating_takes_the_governing_of_rms_and_peak_over_overload():
    s = build_drive_limited_schedule(Product(300, 25), 518.0, 2.0, LIMIT)
    c = torque_chain(s, 9.8, 60.0, 518.0, 1280.0)
    m = motor_sizing(c, 999.0)
    assert m.recommended_rated_kw == pytest.approx(max(m.rms_kw, m.peak_kw / 2.0))


def test_nameplate_is_impossible_single_phase_but_consistent_three_phase():
    """REGRESSION ON A CORRECTED CONCLUSION.

    The 2026-09-19 independent review called 420 V / 2300 A / 1250 kW
    impossible. That verdict was computed SINGLE-PHASE. Three-phase the same
    nameplate implies pf 0.79, which is ordinary for a wound-rotor machine.
    This test pins both results so the correction cannot be lost again.
    """
    r = electrical_consistency(420.0, 2300.0, 3, 1250.0)
    assert not r["consistent_1ph"]
    assert r["implied_pf_1ph"] > 1.0          # physically impossible
    assert r["consistent_3ph"]
    assert 0.75 < r["implied_pf_3ph"] < 0.82


def test_999_rpm_sits_at_six_pole_synchronous_speed():
    """A loaded wound-rotor machine slips below synchronous. 999 rpm is
    essentially the synchronous figure, so it is very likely a no-load or
    nominal value rather than the full-load speed."""
    assert synchronous_speed_rpm(6, 50.0) == pytest.approx(1000.0)
    assert abs(999.0 - synchronous_speed_rpm(6, 50.0)) < 2.0


# --- mass flow --------------------------------------------------------------
def test_mass_flow_speeds_rise_as_the_section_thins():
    v = mass_flow_speed_schedule([(60.0, 250.0), (30.0, 280.0), (12.0, 300.0)], 4.0)
    assert v == sorted(v)
    assert v[-1] == pytest.approx(4.0)


def test_mass_flow_is_conserved_across_the_train():
    secs = [(60.0, 250.0), (30.0, 280.0), (12.0, 300.0)]
    v = mass_flow_speed_schedule(secs, 4.0)
    flows = [h * b * s for (h, b), s in zip(secs, v)]
    assert max(flows) == pytest.approx(min(flows))


def test_mass_flow_rejects_empty_input():
    with pytest.raises(ValueError):
        mass_flow_speed_schedule([], 1.0)


# --- discipline -------------------------------------------------------------
def test_release_blockers_are_declared_and_not_empty():
    assert len(RELEASE_BLOCKERS) >= 10
    joined = " ".join(RELEASE_BLOCKERS)
    for must in ("stand rated force", "gearbox rated torque", "groove geometry",
                 "process temperature", "handling time"):
        assert must in joined
