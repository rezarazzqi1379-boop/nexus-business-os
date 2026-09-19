import math

import pytest

from rolling_mill_mechanics import (
    mass_flow_mismatch_ratio,
    roll_surface_speed_mm_s,
    stand_output_shaft_rpm,
)


# ---------------------------------------------------------------------------
# stand_output_shaft_rpm
# ---------------------------------------------------------------------------

def test_output_shaft_rpm_st1_confirmed_nameplate_values():
    # ST1: motor 999 rpm, gearbox 1:9.8 (confirmed nameplate/CAD data).
    rpm = stand_output_shaft_rpm(999, 1, 9.8)
    assert rpm == pytest.approx(999 / 9.8)


def test_output_shaft_rpm_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        stand_output_shaft_rpm(0, 1, 9.8)
    with pytest.raises(ValueError):
        stand_output_shaft_rpm(999, 1, -9.8)


# ---------------------------------------------------------------------------
# roll_surface_speed_mm_s
# ---------------------------------------------------------------------------

def test_roll_surface_speed_st1_confirmed_nameplate_values():
    # ST1: motor 999rpm, gearbox 1:9.8, roll diameter 518mm (radius 259mm) --
    # all confirmed values from the CAD drawing + engineer's texted nameplate.
    speed = roll_surface_speed_mm_s(999, 1, 9.8, roll_radius_mm=259)
    output_rpm = 999 / 9.8
    expected_mm_per_min = math.pi * 518 * output_rpm
    assert speed == pytest.approx(expected_mm_per_min / 60.0)


def test_roll_surface_speed_matches_manual_formula_for_a_simple_case():
    # 1:1 gearbox, 60 rpm motor, 1000mm diameter roll -> exactly pi*1000*60/60
    # = pi*1000 mm/s.
    speed = roll_surface_speed_mm_s(60, 1, 1, roll_radius_mm=500)
    assert speed == pytest.approx(math.pi * 1000.0)


def test_roll_surface_speed_scales_inversely_with_gearbox_reduction():
    fast = roll_surface_speed_mm_s(1000, 1, 5, roll_radius_mm=300)
    slow = roll_surface_speed_mm_s(1000, 1, 10, roll_radius_mm=300)
    assert fast == pytest.approx(slow * 2)


def test_roll_surface_speed_rejects_non_positive_roll_radius():
    with pytest.raises(ValueError):
        roll_surface_speed_mm_s(999, 1, 9.8, roll_radius_mm=0)


# ---------------------------------------------------------------------------
# mass_flow_mismatch_ratio
# ---------------------------------------------------------------------------

def test_mass_flow_ratio_is_one_when_flow_is_conserved():
    # Same volumetric flow both sides: 100mm/s * 20mm * 300mm == 200mm/s * 10mm * 300mm
    ratio = mass_flow_mismatch_ratio(
        upstream_speed_mm_s=100, upstream_thickness_mm=20, upstream_width_mm=300,
        downstream_speed_mm_s=200, downstream_thickness_mm=10, downstream_width_mm=300,
    )
    assert ratio == pytest.approx(1.0)


def test_mass_flow_ratio_flags_a_real_mismatch():
    ratio = mass_flow_mismatch_ratio(
        upstream_speed_mm_s=100, upstream_thickness_mm=20, upstream_width_mm=300,
        downstream_speed_mm_s=150, downstream_thickness_mm=10, downstream_width_mm=300,
    )
    # downstream flow is 3/4 of what continuity would require
    assert ratio == pytest.approx(0.75)


def test_mass_flow_ratio_rejects_non_positive_inputs():
    with pytest.raises(ValueError):
        mass_flow_mismatch_ratio(
            upstream_speed_mm_s=0, upstream_thickness_mm=20, upstream_width_mm=300,
            downstream_speed_mm_s=150, downstream_thickness_mm=10, downstream_width_mm=300,
        )


# ---------------------------------------------------------------------------
# Confirmed-nameplate reference values for this project's actual 4 stands.
# These are legitimate derived FACTS from confirmed nameplate/CAD data (motor
# rpm, gearbox ratio, roll diameter) -- not a process/pass-schedule
# recommendation. ST2 is skipped: its motor rpm is still not confirmed.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "stand_id,motor_rpm,gearbox_output,roll_diameter_mm,expected_output_rpm",
    [
        ("ST1", 999, 9.8, 518, 999 / 9.8),
        ("ST3", 1000, 8.6, 600, 1000 / 8.6),
        ("ST4", 1000, 5.6, 600, 1000 / 5.6),
    ],
)
def test_confirmed_stand_output_rpm_matches_intake_nameplate_data(
    stand_id, motor_rpm, gearbox_output, roll_diameter_mm, expected_output_rpm
):
    rpm = stand_output_shaft_rpm(motor_rpm, 1, gearbox_output)
    assert rpm == pytest.approx(expected_output_rpm)
