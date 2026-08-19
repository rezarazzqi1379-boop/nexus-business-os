from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


ProviderState = Literal["healthy", "degraded", "blocked", "unknown"]


@dataclass(frozen=True)
class ProviderRoute:
    provider_id: str
    capability: str
    state: ProviderState
    priority: int
    can_read: bool
    can_write: bool
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RouteDecision:
    selected_provider_id: str | None
    attempted_provider_ids: tuple[str, ...]
    blocked_provider_ids: tuple[str, ...]
    reason: str


def _usable(route: ProviderRoute, *, write_required: bool) -> bool:
    if route.state != "healthy":
        return False
    if not route.evidence_refs:
        return False
    if write_required:
        return route.can_write
    return route.can_read


def choose_provider_route(
    routes: Sequence[ProviderRoute],
    *,
    capability: str,
    write_required: bool = False,
) -> RouteDecision:
    """Select the best verified route and fail over deterministically.

    Degraded/blocked/unknown routes are never selected merely because they have a
    better nominal priority. This lets NEXUS keep working when a preferred vendor
    or connector breaks while preserving fail-closed behavior for write actions.
    """
    candidates = [r for r in routes if isinstance(r, ProviderRoute) and r.capability == capability]
    ordered = sorted(candidates, key=lambda r: (r.priority, r.provider_id))
    attempted: list[str] = []
    blocked: list[str] = []

    seen_ids: set[str] = set()
    for route in ordered:
        if route.provider_id in seen_ids:
            blocked.append(route.provider_id)
            continue
        seen_ids.add(route.provider_id)
        attempted.append(route.provider_id)
        if _usable(route, write_required=write_required):
            return RouteDecision(route.provider_id, tuple(attempted), tuple(blocked), "selected first verified healthy route")
        blocked.append(route.provider_id)

    return RouteDecision(None, tuple(attempted), tuple(blocked), "no verified healthy route satisfies requested capability")
