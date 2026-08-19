from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

Capability = Literal["read", "write", "search", "send", "crm", "research", "storage", "code", "workflow", "analytics"]
Health = Literal["healthy", "degraded", "blocked", "unknown"]


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


def _validate_route(route: ConnectorRoute) -> None:
    if not route.name.strip():
        raise ValueError("invalid_route_name")
    if len(route.capabilities) != len(set(route.capabilities)):
        raise ValueError("duplicate_capabilities")
    if route.latency_ms is not None and route.latency_ms < 0:
        raise ValueError("invalid_latency")
    if not 0 <= route.cost_score <= 100:
        raise ValueError("invalid_cost_score")
    if not 0 <= route.reliability_score <= 100:
        raise ValueError("invalid_reliability_score")


def choose_route(routes: Iterable[ConnectorRoute], required: Capability, *, consequential_write: bool = False) -> RouteDecision:
    items = tuple(routes)
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
        if consequential_write and required not in {"write", "send"}:
            raise ValueError("consequential_write_requires_write_capability")
        eligible.append(route)
    if not eligible:
        return RouteDecision(None, (), "no_healthy_capable_route")
    eligible.sort(key=lambda r: (r.priority, -r.reliability_score, r.latency_ms if r.latency_ms is not None else 10**9, r.cost_score, r.name))
    return RouteDecision(eligible[0].name, tuple(r.name for r in eligible[1:]), None)
