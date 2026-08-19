import pytest

from nexus_core.sla_registry import SLO, build_sla_registry
from nexus_core.latency_telemetry import RouteSample, summarize_route
from nexus_core.dynamic_parallelism import choose_parallelism


def test_registry_rejects_duplicates_and_invalid_targets():
    good = SLO("exa", "interactive", 1000, .99, .05, 4)
    with pytest.raises(ValueError):
        build_sla_registry((good, good))
    with pytest.raises(ValueError):
        build_sla_registry((SLO("bad", "interactive", 0, .99, .05, 1),))


def test_telemetry_computes_p50_p95_and_cache_rate():
    samples = tuple(RouteSample("exa", x, True, x % 2 == 0, 100) for x in range(1, 21))
    t = summarize_route(samples)
    assert t.sample_count == 20
    assert t.p50_ms == 10
    assert t.p95_ms == 19
    assert t.error_rate == 0
    assert t.cache_hit_rate == .5


def test_controller_scales_up_only_with_headroom():
    slo = SLO("route", "interactive", 1000, .99, .05, 4)
    fast = summarize_route(tuple(RouteSample("route", 500, True) for _ in range(10)))
    assert choose_parallelism(fast, slo, current_parallelism=2).selected_parallelism == 3


def test_controller_reduces_on_p95_or_error_budget():
    slo = SLO("route", "interactive", 1000, .99, .05, 8)
    slow = summarize_route(tuple(RouteSample("route", 1500, True) for _ in range(10)))
    assert choose_parallelism(slow, slo, current_parallelism=4).selected_parallelism == 3
    noisy = summarize_route(tuple(RouteSample("route", 100, i > 1) for i in range(10)))
    assert choose_parallelism(noisy, slo, current_parallelism=4).selected_parallelism == 2


def test_route_mismatch_fails_closed():
    slo = SLO("a", "interactive", 1000, .99, .05, 4)
    t = summarize_route(tuple(RouteSample("b", 100, True) for _ in range(5)))
    with pytest.raises(ValueError):
        choose_parallelism(t, slo, current_parallelism=2)
