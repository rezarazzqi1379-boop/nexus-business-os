from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Literal

NetworkChange = Literal["none", "ip_changed", "asn_changed", "country_changed", "vpn_changed", "unknown"]
AuthMode = Literal["oauth", "api_key", "session_cookie", "service_account", "unknown"]
ConnectorState = Literal["healthy", "degraded", "reauth_required", "blocked", "unknown"]


@dataclass(frozen=True)
class NetworkContext:
    observed_at: datetime
    public_ip: str | None = None
    asn: str | None = None
    country: str | None = None
    vpn_active: bool | None = None


@dataclass(frozen=True)
class ConnectorNetworkPolicy:
    connector: str
    auth_mode: AuthMode
    ip_allowlist_enforced: bool = False
    geo_sensitive: bool = False
    session_bound_risk: bool = False
    supports_reauth: bool = True


@dataclass(frozen=True)
class NetworkDecision:
    connector: str
    state: ConnectorState
    action: str
    reason: str


def detect_network_change(previous: NetworkContext | None, current: NetworkContext) -> NetworkChange:
    if current.observed_at.tzinfo is None:
        raise ValueError("timezone_naive_current")
    if previous is None:
        return "unknown"
    if previous.observed_at.tzinfo is None:
        raise ValueError("timezone_naive_previous")
    if current.observed_at < previous.observed_at:
        raise ValueError("network_time_reversal")
    if previous.country and current.country and previous.country != current.country:
        return "country_changed"
    if previous.asn and current.asn and previous.asn != current.asn:
        return "asn_changed"
    if previous.vpn_active is not None and current.vpn_active is not None and previous.vpn_active != current.vpn_active:
        return "vpn_changed"
    if previous.public_ip and current.public_ip and previous.public_ip != current.public_ip:
        return "ip_changed"
    return "none"


def evaluate_connector_after_network_change(
    policy: ConnectorNetworkPolicy,
    change: NetworkChange,
    *,
    last_success_at: datetime | None,
    now: datetime,
    auth_error: str | None = None,
) -> NetworkDecision:
    if now.tzinfo is None:
        raise ValueError("timezone_naive_now")
    if not policy.connector.strip():
        raise ValueError("invalid_connector")
    if last_success_at is not None:
        if last_success_at.tzinfo is None:
            raise ValueError("timezone_naive_last_success")
        if last_success_at > now:
            raise ValueError("future_last_success")

    err = (auth_error or "").lower()
    if "ip_not_authorized" in err or (policy.ip_allowlist_enforced and change in {"ip_changed", "asn_changed", "country_changed", "vpn_changed"}):
        return NetworkDecision(policy.connector, "blocked", "check_ip_allowlist", "network_not_allowed")
    if any(token in err for token in ("invalid_grant", "invalid_token", "reauth", "unauthorized", "401")):
        state: ConnectorState = "reauth_required" if policy.supports_reauth else "blocked"
        return NetworkDecision(policy.connector, state, "reauthenticate", "authentication_invalid")
    if policy.geo_sensitive and change == "country_changed":
        return NetworkDecision(policy.connector, "degraded", "probe_before_write", "country_change_risk")
    if policy.session_bound_risk and change in {"asn_changed", "vpn_changed", "country_changed"}:
        return NetworkDecision(policy.connector, "degraded", "refresh_session_and_probe", "session_context_changed")
    if change == "unknown":
        return NetworkDecision(policy.connector, "unknown", "read_probe", "network_baseline_missing")
    if last_success_at is None or now - last_success_at > timedelta(hours=24):
        return NetworkDecision(policy.connector, "degraded", "read_probe", "health_stale")
    return NetworkDecision(policy.connector, "healthy", "continue", "no_network_block_detected")
