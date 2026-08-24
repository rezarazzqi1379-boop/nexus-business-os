from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    available: bool
    read_only: bool
    auth_error: bool
    cost_per_query: float
    evidence_ref: str


@dataclass(frozen=True)
class SourceRoute:
    selected: tuple[str, ...]
    skipped: tuple[tuple[str, str], ...]


def _validate(source: SourceHealth) -> None:
    if not source.source_id.strip() or not source.evidence_ref.strip():
        raise ValueError("invalid_source_health")
    if not isinstance(source.available, bool) or not isinstance(source.read_only, bool) or not isinstance(source.auth_error, bool):
        raise ValueError("invalid_source_boolean")
    if isinstance(source.cost_per_query, bool) or not isinstance(source.cost_per_query, (int, float)) or source.cost_per_query < 0:
        raise ValueError("invalid_source_cost")


def route_read_sources(
    sources: Iterable[SourceHealth], *, max_sources: int = 3, max_cost: float = 0.0
) -> SourceRoute:
    """Select healthy read-only sources; unavailable/auth-broken providers never block the lane."""
    if not 1 <= max_sources <= 10 or max_cost < 0:
        raise ValueError("invalid_route_budget")
    items = tuple(sources)
    seen: set[str] = set()
    selected: list[str] = []
    skipped: list[tuple[str, str]] = []
    spent = 0.0
    for source in sorted(items, key=lambda item: (item.cost_per_query, item.source_id)):
        _validate(source)
        if source.source_id in seen:
            raise ValueError("duplicate_source_health")
        seen.add(source.source_id)
        if source.auth_error:
            skipped.append((source.source_id, "authentication_failed"))
        elif not source.available:
            skipped.append((source.source_id, "unavailable"))
        elif not source.read_only:
            skipped.append((source.source_id, "write_scope_not_allowed"))
        elif spent + source.cost_per_query > max_cost:
            skipped.append((source.source_id, "cost_budget_exceeded"))
        elif len(selected) >= max_sources:
            skipped.append((source.source_id, "source_limit"))
        else:
            selected.append(source.source_id)
            spent += source.cost_per_query
    if not selected:
        skipped.append(("route", "no_safe_source"))
    return SourceRoute(tuple(selected), tuple(skipped))
