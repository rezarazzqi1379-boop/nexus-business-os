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


def test_rejects_runtime_type_confusion_and_unsupported_values():
    with pytest.raises(ValueError):
        choose_route([ConnectorRoute("a", ("read",), "healthy", True, 1, 100)], "read")
    with pytest.raises(ValueError):
        choose_route([ConnectorRoute("a", ("read",), "healthy", 1, True, 100)], "read")
    with pytest.raises(ValueError):
        choose_route([ConnectorRoute("a", ("read",), "mystery", 1, 1, 100)], "read")
    with pytest.raises(ValueError):
        choose_route([ConnectorRoute("a", ("bogus",), "healthy", 1, 1, 100)], "read")


def test_consequential_write_request_is_validated_before_route_selection():
    with pytest.raises(ValueError):
        choose_route([], "research", consequential_write=True)
    with pytest.raises(ValueError):
        choose_route([], "send", consequential_write=1)


def test_non_iterable_routes_fail_closed():
    with pytest.raises(ValueError):
        choose_route(None, "read")


def test_consequential_send_never_returns_a_route_before_policy_gate():
    routes = [ConnectorRoute("gmail", ("send",), "healthy", 10, 1, 100)]
    decision = choose_route(routes, "send", consequential_write=True)
    assert decision.selected is None
    assert decision.fallbacks == ()
    assert decision.blocked_reason == "consequential_write_requires_policy_gate"
