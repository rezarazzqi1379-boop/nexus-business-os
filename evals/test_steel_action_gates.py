"""Gate tests + regression barrier against the obsolete 2026-09-14 intake data."""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from steel_action_gates import (
    PLAUSIBLE_MM, SteelActionGates, detect_obsolete_values, evaluate, to_mm,
)

INTAKE = Path(__file__).resolve().parents[1] / ".nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json"


def real_intake() -> dict:
    return json.loads(INTAKE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Unit normalisation
# ---------------------------------------------------------------------------

def test_to_mm_normalises_metric_units():
    assert to_mm(518, "mm") == 518.0
    assert to_mm(51.8, "cm") == 518.0
    assert to_mm(0.518, "m") == pytest.approx(518.0)


def test_to_mm_refuses_unreadable_input():
    assert to_mm(518, "inch") is None
    assert to_mm("518", "mm") is None
    assert to_mm(True, "mm") is None


# ---------------------------------------------------------------------------
# REGRESSION BARRIER - the obsolete 2026-09-14 values must never go active again
# ---------------------------------------------------------------------------

def test_real_intake_has_no_obsolete_active_values():
    assert detect_obsolete_values(real_intake()) == ()


def test_obsolete_billet_220x220_is_rejected():
    d = real_intake()
    d["product"]["input_billet"]["cross_section_mm"] = {"width": 220, "height": 220}
    assert any("220x220" in v for v in detect_obsolete_values(d))


def test_obsolete_billet_length_3000_is_rejected():
    d = real_intake()
    d["product"]["input_billet"]["length_mm"] = 3000
    assert any("3000mm is the superseded" in v for v in detect_obsolete_values(d))


def test_roll_diameter_550_cm_is_rejected_as_unit_error():
    """5500mm is not a roll, it is a transcription error. Must fail closed."""
    d = real_intake()
    d["mill"]["rolls"]["reported_diameter_around"] = {"value": 550, "unit": "cm"}
    violations = detect_obsolete_values(d)
    assert any("5500mm" in v and "transcription" in v for v in violations)


def test_barrel_length_1350_cm_is_rejected_as_unit_error():
    d = real_intake()
    d["mill"]["rolls"]["barrel_length"] = {"value": 1350, "unit": "cm"}
    assert any("13500mm" in v and "transcription" in v for v in detect_obsolete_values(d))


def test_null_motor_power_is_rejected():
    d = real_intake()
    d["drive"]["motor"]["rated_power_kw"] = None
    assert any("rated_power_kw is null" in v for v in detect_obsolete_values(d))


def test_obsolete_gearbox_ratio_10_to_1_is_rejected():
    d = real_intake()
    d["drive"]["gearbox"]["ratio"] = {"input": 10, "output": 1}
    assert any("10:1 is the superseded" in v for v in detect_obsolete_values(d))


def test_the_correct_518mm_reading_passes_cleanly():
    d = real_intake()
    assert d["mill"]["rolls"]["reported_diameter_around"]["value"] == 518
    assert d["mill"]["rolls"]["reported_diameter_around"]["unit"] == "mm"
    assert detect_obsolete_values(d) == ()


def test_preserved_historical_readings_do_not_trip_the_guard():
    """The 550 and 1350 readings are deliberately retained as evidence history.
    Preserving them is required; the guard must only reject them as ACTIVE values."""
    d = real_intake()
    flat = json.dumps(d, ensure_ascii=False)
    assert "550" in flat and "1350" in flat, "historical readings must still be preserved"
    assert detect_obsolete_values(d) == ()


def test_every_obsolete_value_also_blocks_concept_calculation():
    """Computing on a known-wrong machine is worse than not computing."""
    d = real_intake()
    d["product"]["input_billet"]["cross_section_mm"] = {"width": 220, "height": 220}
    g = evaluate(d)
    assert g.concept_calculation_allowed is False
    assert g.fabrication_release_allowed is False
    assert any("obsolete/implausible" in b for b in g.concept_blockers)


# ---------------------------------------------------------------------------
# The two gates are genuinely independent
# ---------------------------------------------------------------------------

def test_current_data_permits_concept_but_not_fabrication():
    g = evaluate(real_intake())
    assert g.concept_calculation_allowed is True
    assert g.fabrication_release_allowed is False


def test_fabrication_blockers_name_the_real_missing_items():
    g = evaluate(real_intake())
    joined = " ".join(g.fabrication_blockers)
    for expected in ("limits.maximum_roll_force_n", "mill.rolls.roll_material",
                     "process.historical_successful_run_locator",
                     "independent_engineering_review.verdict",
                     "safety.guards_verified"):
        assert expected in joined, f"{expected} should block fabrication release"


def test_fabrication_stays_closed_even_when_everything_else_is_filled():
    """Safety must be explicitly true - filling the paperwork is not enough."""
    d = real_intake()
    d["limits"] = {"maximum_roll_force_n": 3_000_000, "maximum_spindle_torque_nm": 200_000,
                   "maximum_motor_current_a": 2500}
    d["drive"]["gearbox"]["rated_output_torque_nm"] = 150_000
    d["process"]["reheating_temperature_degC"] = 1150
    d["process"]["historical_successful_run_locator"] = "doc:run-2026-01-01"
    d["mill"]["rolls"]["roll_material"] = "forged steel, 55 HSD"
    d["independent_engineering_review"] = {"verdict": "ACCEPT"}
    g = evaluate(d)
    assert g.fabrication_release_allowed is False
    assert any("guards_verified" in b for b in g.fabrication_blockers)


def test_fabrication_can_open_only_when_every_prerequisite_is_recorded():
    d = real_intake()
    d["limits"] = {"maximum_roll_force_n": 3_000_000, "maximum_spindle_torque_nm": 200_000,
                   "maximum_motor_current_a": 2500}
    d["drive"]["gearbox"]["rated_output_torque_nm"] = 150_000
    d["process"]["reheating_temperature_degC"] = 1150
    d["process"]["historical_successful_run_locator"] = "doc:run-2026-01-01"
    d["mill"]["rolls"]["roll_material"] = "forged steel, 55 HSD"
    d["independent_engineering_review"] = {"verdict": "ACCEPT"}
    d["safety"] = {"guards_verified": True, "emergency_stops_verified": True,
                   "loto_procedure_locator": "doc:loto-v1"}
    g = evaluate(d)
    assert g.fabrication_release_allowed is True
    # even then the gate must not claim to be the authorisation itself
    assert "owner's" in g.next_gate and "does not grant it" in g.next_gate


def test_missing_drive_data_blocks_concept():
    d = real_intake()
    d["drive"]["motor"]["rated_speed_rpm"] = None
    g = evaluate(d)
    assert g.concept_calculation_allowed is False


def test_require_concept_raises_when_blocked():
    d = real_intake()
    d["product"]["input_billet"]["length_mm"] = 3000
    with pytest.raises(PermissionError, match="concept calculation not permitted"):
        evaluate(d).require_concept()


def test_require_concept_passes_on_current_data():
    evaluate(real_intake()).require_concept()  # must not raise


def test_gate_result_is_immutable():
    g = evaluate(real_intake())
    with pytest.raises(Exception):
        g.concept_calculation_allowed = False  # type: ignore[misc]


def test_plausibility_bands_are_documented_and_ordered():
    for name, (lo, hi) in PLAUSIBLE_MM.items():
        assert 0 < lo < hi, f"{name} band must be a positive ordered range"


def test_evaluate_does_not_mutate_the_payload():
    d = real_intake()
    before = copy.deepcopy(d)
    evaluate(d)
    assert d == before
