import math
import pytest
from thermal_and_route_model import (Section, billet_section, cool_transit, h_convection,
    route_metrics, ROUTE_A, ROUTE_B2, ROUTE_C1, Feedstock, RHO)


def test_billet_mass_matches_recorded_intake_value():
    b = billet_section()
    assert b.mass_kg == pytest.approx(556.4, abs=0.5)
    assert b.length_m == pytest.approx(3.15)


def test_section_conserves_volume_when_rolled_thinner():
    v = billet_section().volume_m3
    thin = Section(8.0, 300.0, v)
    assert thin.volume_m3 == pytest.approx(v)
    assert thin.length_m == pytest.approx(v / 0.0024, rel=1e-9)
    assert thin.mass_kg == pytest.approx(billet_section().mass_kg)


def test_surface_to_mass_ratio_rises_sharply_as_section_thins():
    """The physical reason the engineer's 950->800 window is short."""
    v = billet_section().volume_m3
    thick = billet_section(); thin = Section(8.0, 300.0, v)
    assert thin.surface_m2 / thin.mass_kg > 9 * (thick.surface_m2 / thick.mass_kg)


def test_radiation_dominates_convection_at_rolling_temperature():
    r = cool_transit(billet_section(), 1250.0, 12.0, 1.0)
    assert r["rad_flux_kw_m2"] > 10 * r["con_flux_kw_m2"]


def test_cooling_drop_scales_with_transit_time():
    slow = cool_transit(billet_section(), 1250.0, 12.0, 0.5)
    fast = cool_transit(billet_section(), 1250.0, 12.0, 2.0)
    assert slow["transit_s"] == pytest.approx(4 * fast["transit_s"])
    assert slow["mean_drop_c"] > 3 * fast["mean_drop_c"]


def test_billet_is_not_lumped_but_thin_strip_is():
    """Regression: a pyrometer reads the SURFACE. For the billet the lumped
    model is invalid (Bi>0.1), so surface and mean are different numbers."""
    assert not cool_transit(billet_section(), 1250.0, 12.0, 1.0)["lumped_valid"]
    v = billet_section().volume_m3
    assert cool_transit(Section(25.0, 250.0, v), 1200.0, 21.0, 1.0)["lumped_valid"]


def test_cover_reduces_but_does_not_eliminate_loss():
    open_ = cool_transit(billet_section(), 1250.0, 12.0, 0.5)
    covered = cool_transit(billet_section(), 1250.0, 12.0, 0.5, covered=True)
    assert 0 < covered["mean_drop_c"] < open_["mean_drop_c"]


def test_engineer_declared_12m_drop_requires_a_slow_transfer():
    """CLAIM under test: 1250 C -> 1200 C over 12 m.
    50 K is reachable only at the slow end of the speed range."""
    at_1_m_s = cool_transit(billet_section(), 1250.0, 12.0, 1.0)["mean_drop_c"]
    at_025 = cool_transit(billet_section(), 1250.0, 12.0, 0.25)["mean_drop_c"]
    assert at_1_m_s < 50.0 < at_025


def test_velocity_must_be_positive():
    with pytest.raises(ValueError):
        cool_transit(billet_section(), 1200.0, 12.0, 0.0)


def test_h_convection_increases_with_velocity():
    assert h_convection(2.0) > h_convection(0.0)


def test_reduction_ratio_collapses_at_wide_thick_product():
    """The economic hypothesis under test: 'closer input is simpler'.
    From the CURRENT billet, 600x30 leaves almost no reduction at all."""
    m = route_metrics(ROUTE_A, 30.0, 600.0)
    assert m["reduction_ratio"] < 1.5
    assert route_metrics(ROUTE_A, 8.0, 300.0)["reduction_ratio"] > 9.0


def test_slab_route_removes_the_width_problem_but_kills_reduction_ratio():
    slab = route_metrics(ROUTE_C1, 30.0, 300.0)
    billet = route_metrics(ROUTE_A, 30.0, 300.0)
    assert slab["width_ratio"] < 1.0 < billet["width_ratio"]
    assert slab["reduction_ratio"] < billet["reduction_ratio"]


def test_product_length_grows_as_product_thins():
    long_ = route_metrics(ROUTE_A, 8.0, 300.0)["product_length_m"]
    short = route_metrics(ROUTE_A, 30.0, 300.0)["product_length_m"]
    assert long_ > 28.0 > short
    assert long_ / short == pytest.approx(30.0 / 8.0, rel=1e-6)


def test_bloom_route_restores_reduction_ratio_at_600mm():
    assert route_metrics(ROUTE_B2, 30.0, 600.0)["reduction_ratio"] > \
           2.5 * route_metrics(ROUTE_A, 30.0, 600.0)["reduction_ratio"]


def test_mass_balance_closes():
    f = Feedstock("t", 150, 150, 3150, "test")
    m = route_metrics(f, 25.0, 300.0, yield_fraction=1.0)
    out_vol = m["product_length_m"] * (25 * 300 / 1e6)
    assert out_vol == pytest.approx(f.volume_m3, rel=1e-9)
