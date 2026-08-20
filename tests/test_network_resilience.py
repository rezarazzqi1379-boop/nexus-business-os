from datetime import datetime, timezone, timedelta
import pytest

from nexus_core.network_resilience import NetworkContext, ConnectorNetworkPolicy, detect_network_change, evaluate_connector_after_network_change


def test_ip_change_does_not_break_oauth_without_allowlist():
    t = datetime(2026, 8, 20, tzinfo=timezone.utc)
    prev = NetworkContext(t, public_ip="1.1.1.1", country="IR")
    cur = NetworkContext(t + timedelta(minutes=1), public_ip="2.2.2.2", country="IR")
    assert detect_network_change(prev, cur) == "ip_changed"
    decision = evaluate_connector_after_network_change(
        ConnectorNetworkPolicy("gmail", "oauth"),
        "ip_changed",
        last_success_at=t,
        now=t + timedelta(minutes=2),
    )
    assert decision.state == "healthy"


def test_allowlist_blocks_changed_network():
    t = datetime(2026, 8, 20, tzinfo=timezone.utc)
    d = evaluate_connector_after_network_change(
        ConnectorNetworkPolicy("api", "api_key", ip_allowlist_enforced=True),
        "ip_changed",
        last_success_at=t,
        now=t + timedelta(minutes=1),
    )
    assert d.state == "blocked"
    assert d.action == "check_ip_allowlist"


def test_401_routes_to_reauth():
    t = datetime(2026, 8, 20, tzinfo=timezone.utc)
    d = evaluate_connector_after_network_change(
        ConnectorNetworkPolicy("hubspot", "oauth"), "none", last_success_at=t, now=t, auth_error="401 Unauthorized"
    )
    assert d.state == "reauth_required"


def test_network_time_reversal_fails_closed():
    t = datetime(2026, 8, 20, tzinfo=timezone.utc)
    with pytest.raises(ValueError):
        detect_network_change(NetworkContext(t), NetworkContext(t - timedelta(seconds=1)))
