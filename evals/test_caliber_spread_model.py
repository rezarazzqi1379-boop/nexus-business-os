"""IC-02 tests. The instrument must discriminate deformation modes, refuse
anonymous data, and never let synthetic input masquerade as a real finding."""
import pytest

from caliber_spread_model import (
    ACCEPTANCE_TOLERANCE_PCT, CaliberModel, PassMeasurement, PassMode, SYNTHETIC_PREFIX,
    WidthMechanism, acceptance_check, analyse_pass_width, diagnose_width_mechanism,
    fit_caliber_model, synthetic_edging_run, synthetic_flat_run, synthetic_grooved_run,
)


def m(**kw):
    base = dict(pass_index=1, entry_thickness_mm=150.0, exit_thickness_mm=130.0,
                entry_width_mm=150.0, exit_width_mm=158.0, roll_diameter_mm=518.0,
                source=f"{SYNTHETIC_PREFIX}unit test")
    base.update(kw)
    return PassMeasurement(**base)


# --------------------------------------------------------------------------
# Evidence discipline
# --------------------------------------------------------------------------

def test_measurement_requires_a_source_locator():
    with pytest.raises(ValueError, match="no anonymous data"):
        m(source="").validate()
    with pytest.raises(ValueError, match="no anonymous data"):
        m(source="   ").validate()


def test_synthetic_data_is_flagged_and_forces_illustrative_only():
    result = diagnose_width_mechanism(synthetic_grooved_run())
    assert result["illustrative_only"] is True
    assert any("ILLUSTRATIVE_ONLY" in w for w in result["warnings"])


def test_real_sourced_data_is_not_marked_illustrative():
    rows = [(150.0, 128.0, 150.0, 168.0), (128.0, 108.0, 168.0, 186.0)]
    real = [PassMeasurement(pass_index=i + 1, entry_thickness_mm=r[0], exit_thickness_mm=r[1],
                            entry_width_mm=r[2], exit_width_mm=r[3], roll_diameter_mm=518.0,
                            source="video:2026-10-01 shift A, frame 1420", temperature_c=1100.0)
            for i, r in enumerate(rows)]
    assert fit_caliber_model(real).illustrative_only is False


def test_missing_temperature_raises_a_confound_warning():
    rows = [(150.0, 128.0, 150.0, 168.0), (128.0, 108.0, 168.0, 186.0)]
    noted = [PassMeasurement(pass_index=i + 1, entry_thickness_mm=r[0], exit_thickness_mm=r[1],
                             entry_width_mm=r[2], exit_width_mm=r[3], roll_diameter_mm=518.0,
                             source="video:real") for i, r in enumerate(rows)]
    assert any("temperature" in w.lower() for w in fit_caliber_model(noted).warnings)


# --------------------------------------------------------------------------
# Input validation - fail closed
# --------------------------------------------------------------------------

@pytest.mark.parametrize("field,value", [
    ("entry_thickness_mm", 0), ("exit_thickness_mm", -1), ("entry_width_mm", 0),
    ("exit_width_mm", -5), ("roll_diameter_mm", 0), ("pass_index", 0),
])
def test_non_physical_values_are_rejected(field, value):
    with pytest.raises(ValueError):
        m(**{field: value}).validate()


def test_a_pass_cannot_increase_thickness():
    with pytest.raises(ValueError, match="cannot increase thickness"):
        m(entry_thickness_mm=100.0, exit_thickness_mm=120.0).validate()


def test_bad_temperature_is_rejected():
    with pytest.raises(ValueError, match="temperature_c"):
        m(temperature_c=0).validate()


def test_fit_needs_at_least_two_passes():
    with pytest.raises(ValueError, match="at least two"):
        fit_caliber_model([m()])


def test_passes_must_be_in_ascending_order():
    a, b = m(pass_index=2), m(pass_index=1)
    with pytest.raises(ValueError, match="ascending pass order"):
        fit_caliber_model([a, b])


# --------------------------------------------------------------------------
# Per-pass classification
# --------------------------------------------------------------------------

def test_free_spread_pass_is_recognised():
    from rolling_line_concept import wusatowski_spread
    nat = wusatowski_spread(150.0, 130.0, 150.0, 518.0)
    d = analyse_pass_width(m(exit_width_mm=nat))
    assert d.mode is PassMode.FREE_SPREAD
    assert d.kappa == pytest.approx(1.0, abs=0.01)


def test_groove_assisted_pass_is_recognised():
    d = analyse_pass_width(m(exit_width_mm=175.0))  # far more width than free spread
    assert d.mode is PassMode.GROOVE_ASSISTED
    assert d.kappa > 1.3


def test_groove_constrained_pass_is_recognised():
    """Thickness falls, width is held - the signature of groove side walls."""
    d = analyse_pass_width(m(exit_width_mm=150.0))
    assert d.mode is PassMode.GROOVE_CONSTRAINED


def test_edging_pass_is_recognised():
    d = analyse_pass_width(m(exit_width_mm=140.0))
    assert d.mode is PassMode.EDGING


# --------------------------------------------------------------------------
# THE CORE DISCRIMINATION - the independent reviewer's question one
# --------------------------------------------------------------------------

def test_grooved_run_is_diagnosed_as_grooved():
    r = diagnose_width_mechanism(synthetic_grooved_run())
    assert r["mechanism"] == WidthMechanism.GROOVED.value
    assert "WRONG deformation mode" in r["verdict"]


def test_flat_run_is_diagnosed_as_flat():
    r = diagnose_width_mechanism(synthetic_flat_run())
    assert r["mechanism"] == WidthMechanism.FLAT_ROLLING.value
    assert r["mean_kappa"] == pytest.approx(1.0, abs=0.02)


def test_edging_run_is_detected():
    r = diagnose_width_mechanism(synthetic_edging_run())
    assert any(p["mode"] == PassMode.EDGING.value for p in r["per_pass"])


def test_flat_model_error_reproduces_the_real_mills_gap():
    """The real mill shows ~183mm predicted vs 250mm actual, about -27%.
    The instrument must surface a gap of that size, not absorb it."""
    r = diagnose_width_mechanism(synthetic_grooved_run())
    assert r["flat_model_error_pct"] < -20.0


def test_flat_run_shows_no_gap():
    r = diagnose_width_mechanism(synthetic_flat_run())
    assert abs(r["flat_model_error_pct"]) < 1.0


# --------------------------------------------------------------------------
# Acceptance criterion
# --------------------------------------------------------------------------

def test_acceptance_passes_on_grooved_data():
    a = acceptance_check(synthetic_grooved_run())
    assert a["passed"] is True
    assert a["reproduces_measurement"] is True
    assert a["discriminates_against_flat_model"] is True
    assert a["fitted_model_error_pct"] <= ACCEPTANCE_TOLERANCE_PCT


def test_acceptance_fails_to_discriminate_on_flat_data():
    """On genuinely flat data there is nothing to discriminate, so the
    instrument must NOT claim a pass - that would be a false positive."""
    a = acceptance_check(synthetic_flat_run())
    assert a["discriminates_against_flat_model"] is False
    assert a["passed"] is False


def test_acceptance_never_claims_the_mill_is_understood():
    a = acceptance_check(synthetic_grooved_run())
    assert "does NOT mean" in a["note"]
    assert "authorises no operating or design change" in a["note"]


# --------------------------------------------------------------------------
# Forward projection - must return a band and a warning, never a design
# --------------------------------------------------------------------------

def test_projection_returns_a_band_not_a_number():
    model = fit_caliber_model(synthetic_grooved_run())
    seq = [(150.0, 128.0), (128.0, 108.0), (108.0, 90.0), (90.0, 74.0)]
    p = model.predict_final_width(150.0, seq, 518.0)
    lo, hi = p["width_band_mm"]
    assert lo < hi, "a projection built on a measured kappa range must be a band"


def test_projection_carries_an_explicit_non_design_warning():
    model = fit_caliber_model(synthetic_grooved_run())
    p = model.predict_final_width(150.0, [(150.0, 128.0), (128.0, 108.0)], 518.0)
    assert "not a caliber design" in p["warning"]
    assert "qualified engineer" in p["warning"]


def test_projection_propagates_the_illustrative_flag():
    model = fit_caliber_model(synthetic_grooved_run())
    p = model.predict_final_width(150.0, [(150.0, 128.0), (128.0, 108.0)], 518.0)
    assert p["illustrative_only"] is True


def test_projection_rejects_bad_inputs():
    model = fit_caliber_model(synthetic_grooved_run())
    with pytest.raises(ValueError):
        model.predict_final_width(0, [(150.0, 128.0)], 518.0)
    with pytest.raises(ValueError):
        model.predict_final_width(150.0, [], 518.0)


def test_projection_with_explicit_kappa_collapses_the_band():
    model = fit_caliber_model(synthetic_grooved_run())
    p = model.predict_final_width(150.0, [(150.0, 128.0), (128.0, 108.0)], 518.0, kappa=3.0)
    lo, hi = p["width_band_mm"]
    assert lo == hi


def test_model_is_immutable():
    model = fit_caliber_model(synthetic_grooved_run())
    with pytest.raises(Exception):
        model.mean_kappa = 99.0  # type: ignore[misc]
