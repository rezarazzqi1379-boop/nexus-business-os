import pytest

from nexus_core.connector_broker import ConnectorRoute, choose_route


def test_selects_healthy_reliable_low_latency_route():
    routes = [
        ConnectorRoute("a", ("research",), "healthy", 300, 10, 90, 10),
        ConnectorRoute("b", ("research",), "healthy", 100, 10, 90, 10),
    ]
    assert choose_route(routes, "research").selected == "b"


def test_degraded_route_is_not_selected():
    routes = [ConnectorRoute("a", ("crm",), "degraded", 10, 1, 100)]
    d = choose_route(routes, "crm")
    assert d.selected is None
    assert d.blocked_reason == "no_healthy_capable_route"


def test_duplicate_route_fails_closed():
    routes = [
        ConnectorRoute("a", ("read",), "healthy", 1, 1, 100),
        ConnectorRoute("a", ("read",), "healthy", 1, 1, 100),
    ]
    with pytest.raises(ValueError):
        choose_route(routes, "read")
