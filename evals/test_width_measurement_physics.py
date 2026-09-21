import math
import pytest
from width_measurement_architectures import A1, A2, A3, A4, A5, ALL
from width_measurement_physics import (
    ALPHA_PER_K, MeasurementArchitecture, can_discriminate, edge_bloom_error_mm,
    hot_to_cold, monte_carlo_kappa, obliquity_error_mm, pixel_resolution_mm,
    required_width_accuracy_mm, temperature_uncertainty_mm, thermal_expansion_mm,
)

W, GAIN, T = 180.0, 8.0, 1050.0


def test_thermal_expansion_is_about_one_and_a_third_percent_at_rolling_heat():
    e = thermal_expansion_mm(W, T)
    assert e == pytest.approx(W * ALPHA_PER_K * (T - 20.0))
    assert 1.0 < 100 * e / W < 1.7


def test_hot_to_cold_inverts_expansion():
    hot = W * (1 + ALPHA_PER_K * (T - 20.0))
    assert hot_to_cold(hot, T) == pytest.approx(W, abs=1e-9)


def test_temperature_uncertainty_scales_with_width_and_dt():
    assert temperature_uncertainty_mm(W, 60) == pytest.approx(2 * temperature_uncertainty_mm(W, 30))
    assert temperature_uncertainty_mm(360, 30) == pytest.approx(2 * temperature_uncertainty_mm(180, 30))


def test_obliquity_always_reads_short_and_grows_with_angle():
    assert obliquity_error_mm(W, 0) == pytest.approx(0.0)
    assert 0 < obliquity_error_mm(W, 3) < obliquity_error_mm(W, 10)


def test_edge_bloom_counts_both_edges():
    px = pixel_resolution_mm(400, 2000)
    assert edge_bloom_error_mm(px, 2.0) == pytest.approx(2 * px * 2.0)


@pytest.mark.parametrize("fn,args", [
    (thermal_expansion_mm, (0, T)), (hot_to_cold, (0, T)),
    (temperature_uncertainty_mm, (0, 30)), (obliquity_error_mm, (0, 5)),
    (pixel_resolution_mm, (0, 100)), (edge_bloom_error_mm, (0, 2)),
])
def test_non_physical_inputs_are_rejected(fn, args):
    with pytest.raises(ValueError):
        fn(*args)


# --- the inverse-design result, which is the point of the module -----------

def test_coarse_question_is_far_easier_than_the_fine_one():
    coarse = required_width_accuracy_mm(67.0, 1.0, 2.0)
    fine = required_width_accuracy_mm(GAIN, 1.0, 1.3)
    assert coarse > 20 * fine, "the two questions must land in different instrument classes"


def test_fine_requirement_is_sub_millimetre():
    assert required_width_accuracy_mm(GAIN, 1.0, 1.3) < 1.0


def test_required_accuracy_tightens_as_natural_gain_collapses():
    """Late passes have almost no free spread, so kappa gets harder to measure."""
    early = required_width_accuracy_mm(8.0, 1.0, 1.3)
    late = required_width_accuracy_mm(1.5, 1.0, 1.3)
    assert late < early / 4


def test_required_accuracy_rejects_degenerate_input():
    with pytest.raises(ValueError):
        required_width_accuracy_mm(8.0, 1.3, 1.3)
    with pytest.raises(ValueError):
        required_width_accuracy_mm(0.0, 1.0, 1.3)


# --- architectures --------------------------------------------------------

def test_architectures_are_ordered_by_error():
    errs = [a.total_error_mm(W)["worst_case_mm"] for a in (A1, A2, A3, A4, A5)]
    assert errs == sorted(errs, reverse=True), "A1 worst, A5 best"


def test_every_architecture_documents_principle_and_cost():
    for a in ALL:
        assert a.principle.strip() and a.cost_class.strip()


def test_at_least_one_architecture_is_locally_buildable_and_resolves_fine_kappa():
    ok = [a for a in ALL if a.buildable_locally
          and can_discriminate(a, W, GAIN, T, trials=800)["resolves_fine_kappa"]]
    assert ok, "there must be a locally buildable option that resolves kappa"


def test_cheapest_option_cannot_resolve_the_fine_threshold():
    assert can_discriminate(A1, W, GAIN, T, trials=2000)["resolves_fine_kappa"] is False


def test_jig_rig_resolves_the_fine_threshold():
    assert can_discriminate(A2, W, GAIN, T, trials=2000)["resolves_fine_kappa"] is True


def test_unconventional_backlight_beats_the_conventional_rig():
    a2 = can_discriminate(A2, W, GAIN, T, trials=2000)["separation_sigma"]
    a3 = can_discriminate(A3, W, GAIN, T, trials=2000)["separation_sigma"]
    assert a3 > a2, "rejecting self-glow should buy real accuracy"


def test_portable_scanner_sample_rate_cannot_follow_a_live_pass_sequence():
    assert A4.sample_rate_hz < 0.2
    assert A2.sample_rate_hz > 10


# --- the headline claim ---------------------------------------------------

def test_cheapest_option_still_separates_the_real_grooved_case_from_flat():
    """The decision-relevant claim: the phone answers the question that matters."""
    r = monte_carlo_kappa(4.72, W, GAIN, A1, T, trials=3000)
    assert r["p05"] > 1.3, "A1 must still exclude flat rolling at the real kappa"


def test_no_architecture_introduces_large_bias_on_kappa():
    for a in ALL:
        r = monte_carlo_kappa(4.72, W, GAIN, a, T, trials=1500)
        assert abs(r["bias"]) < 0.15, f"{a.arch_id} biases kappa"


def test_monte_carlo_refuses_a_meaningless_sample():
    with pytest.raises(ValueError):
        monte_carlo_kappa(4.72, W, GAIN, A2, T, trials=10)


def test_monte_carlo_is_reproducible():
    a = monte_carlo_kappa(4.72, W, GAIN, A2, T, trials=500, seed=5)
    b = monte_carlo_kappa(4.72, W, GAIN, A2, T, trials=500, seed=5)
    assert a == b
