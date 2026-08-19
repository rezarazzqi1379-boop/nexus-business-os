import pytest

from nexus_core.connector_broker import ConnectorRoute
from nexus_core.connector_sla_binding import bind_connector_slas, choose_sla_compliant_route
from nexus_core.latency_telemetry import RouteTelemetry
from nexus_core.sla_registry import SLO


def _route(name: str, *, health: str = "healthy", latency_ms: int = 100, reliability: int = 90):
    return ConnectorRoute(name, ("research",), health, latency_ms, 10, reliability, 10)


def _slo(name: str):
    return SLO(name, "interactive", 1000, .95, .05, 4)


def _telemetry(name: str, *, p95: int = 500, error: float = .01, samples: int = 10):
    return RouteTelemetry(name, samples, 300, p95, error, .2, 100.0)


def test_binding_requires_capability_health_slo_and_fresh_enough_samples():
    route = _route("exa")
    bound = bind_connector_slas(
        (route,),
        required="research",
        sla_registry={"exa": _slo("exa")},
        telemetry=(_telemetry("exa"),),
    )
    assert bound[0].compliant is True
    assert bound[0].reasons == ()


def test_missing_or_under_sampled_telemetry_fails_closed():
    route = _route("exa")
    missing = bind_connector_slas(
        (route,), required="research", sla_registry={"exa": _slo("exa")}, telemetry=()
    )
    assert missing[0].compliant is False
    assert "missing_telemetry" in missing[0].reasons

    thin = bind_connector_slas(
        (route,),
        required="research",
        sla_registry={"exa": _slo("exa")},
        telemetry=(_telemetry("exa", samples=2),),
        minimum_samples=5,
    )
    assert thin[0].compliant is False
    assert "insufficient_samples" in thin[0].reasons


def test_latency_error_and_availability_breaches_block_route():
    route = _route("exa")
    bound = bind_connector_slas(
        (route,),
        required="research",
        sla_registry={"exa": _slo("exa")},
        telemetry=(_telemetry("exa", p95=1500, error=.10),),
    )
    assert bound[0].compliant is False
    assert "p95_target_missed" in bound[0].reasons
    assert "error_budget_exceeded" in bound[0].reasons
    assert "availability_target_missed" in bound[0].reasons


def test_selection_uses_only_sla_compliant_routes_then_existing_route_ordering():
    routes = (
        _route("a", latency_ms=300, reliability=95),
        _route("b", latency_ms=100, reliability=90),
        _route("c", latency_ms=50, reliability=100),
    )
    decision = choose_sla_compliant_route(
        routes,
        required="research",
        sla_registry={name: _slo(name) for name in ("a", "b", "c")},
        telemetry=(
            _telemetry("a"),
            _telemetry("b"),
            _telemetry("c", p95=1500),
        ),
    )
    assert decision.selected == "a"
    assert decision.fallbacks == ("b",)


def test_duplicate_telemetry_and_duplicate_routes_fail_closed():
    with pytest.raises(ValueError):
        bind_connector_slas(
            (_route("a"),),
            required="research",
            sla_registry={"a": _slo("a")},
            telemetry=(_telemetry("a"), _telemetry("a")),
        )
    with pytest.raises(ValueError):
        bind_connector_slas(
            (_route("a"), _route("a")),
            required="research",
            sla_registry={"a": _slo("a")},
            telemetry=(_telemetry("a"),),
        )
