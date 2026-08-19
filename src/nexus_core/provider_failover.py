from __future__ import annotations

from collections import Counter
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

    Duplicate provider IDs are treated as ambiguous control-plane state and are
    removed entirely. A degraded preferred provider therefore cannot block a
    verified secondary route, while write actions still require explicit write
    capability evidence on the selected provider.
    """
    candidates = [r for r in routes if isinstance(r, ProviderRoute) and r.capability == capability]
    counts = Counter(r.provider_id for r in candidates)
    duplicate_ids = {provider_id for provider_id, count in counts.items() if count > 1}
    ordered = sorted(
        (r for r in candidates if r.provider_id not in duplicate_ids),
        key=lambda r: (r.priority, r.provider_id),
    )

    attempted: list[str] = []
    blocked: list[str] = sorted(duplicate_ids)
    for route in ordered:
        attempted.append(route.provider_id)
        if _usable(route, write_required=write_required):
            return RouteDecision(route.provider_id, tuple(attempted), tuple(blocked), "selected first verified healthy route")
        blocked.append(route.provider_id)

    reason = "ambiguous duplicate provider routes" if duplicate_ids and not ordered else "no verified healthy route satisfies requested capability"
    return RouteDecision(None, tuple(attempted), tuple(blocked), reason)
