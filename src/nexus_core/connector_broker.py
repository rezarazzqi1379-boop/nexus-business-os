from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

Capability = Literal["read", "write", "search", "send", "crm", "research", "storage", "code", "workflow", "analytics"]
Health = Literal["healthy", "degraded", "blocked", "unknown"]

_ALLOWED_CAPABILITIES = {"read", "write", "search", "send", "crm", "research", "storage", "code", "workflow", "analytics"}
_ALLOWED_HEALTH = {"healthy", "degraded", "blocked", "unknown"}
_MAX_TEXT = 256


@dataclass(frozen=True)
class ConnectorRoute:
    name: str
    capabilities: tuple[Capability, ...]
    health: Health
    latency_ms: int | None
    cost_score: int
    reliability_score: int
    priority: int = 100


@dataclass(frozen=True)
class RouteDecision:
    selected: str | None
    fallbacks: tuple[str, ...]
    blocked_reason: str | None


def _valid_compact_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= _MAX_TEXT


def _valid_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _validate_route(route: object) -> None:
    if not isinstance(route, ConnectorRoute):
        raise ValueError("invalid_route")
    if not _valid_compact_text(route.name):
        raise ValueError("invalid_route_name")
    if not isinstance(route.capabilities, tuple) or not route.capabilities:
        raise ValueError("invalid_capabilities")
    if len(route.capabilities) != len(set(route.capabilities)):
        raise ValueError("duplicate_capabilities")
    if any(capability not in _ALLOWED_CAPABILITIES for capability in route.capabilities):
        raise ValueError("unsupported_capability")
    if route.health not in _ALLOWED_HEALTH:
        raise ValueError("unsupported_health")
    if route.latency_ms is not None and (not _valid_int(route.latency_ms) or route.latency_ms < 0):
        raise ValueError("invalid_latency")
    if not _valid_int(route.cost_score) or not 0 <= route.cost_score <= 100:
        raise ValueError("invalid_cost_score")
    if not _valid_int(route.reliability_score) or not 0 <= route.reliability_score <= 100:
        raise ValueError("invalid_reliability_score")
    if not _valid_int(route.priority) or route.priority < 0:
        raise ValueError("invalid_priority")


def choose_route(routes: Iterable[ConnectorRoute], required: Capability, *, consequential_write: bool = False) -> RouteDecision:
    if required not in _ALLOWED_CAPABILITIES:
        raise ValueError("unsupported_required_capability")
    if not isinstance(consequential_write, bool):
        raise ValueError("invalid_consequential_write")
    if consequential_write and required not in {"write", "send"}:
        raise ValueError("consequential_write_requires_write_capability")
    if consequential_write:
        return RouteDecision(None, (), "consequential_write_requires_policy_gate")
    try:
        items = tuple(routes)
    except TypeError as exc:
        raise ValueError("routes_must_be_iterable") from exc

    seen: set[str] = set()
    eligible: list[ConnectorRoute] = []
    for route in items:
        _validate_route(route)
        if route.name in seen:
            raise ValueError("duplicate_route_name")
        seen.add(route.name)
        if required not in route.capabilities:
            continue
        if route.health != "healthy":
            continue
        eligible.append(route)
    if not eligible:
        return RouteDecision(None, (), "no_healthy_capable_route")
    eligible.sort(key=lambda r: (r.priority, -r.reliability_score, r.latency_ms if r.latency_ms is not None else 10**9, r.cost_score, r.name))
    return RouteDecision(eligible[0].name, tuple(r.name for r in eligible[1:]), None)
