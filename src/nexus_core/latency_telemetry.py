from __future__ import annotations

from dataclasses import dataclass
from math import ceil
from typing import Iterable


@dataclass(frozen=True)
class RouteSample:
    route_id: str
    latency_ms: int
    success: bool
    cache_hit: bool = False
    context_tokens: int = 0


@dataclass(frozen=True)
class RouteTelemetry:
    route_id: str
    sample_count: int
    p50_ms: int
    p95_ms: int
    error_rate: float
    cache_hit_rate: float
    mean_context_tokens: float


def _percentile(values: list[int], q: float) -> int:
    if not values:
        raise ValueError("empty_samples")
    values = sorted(values)
    idx = max(0, min(len(values) - 1, ceil(q * len(values)) - 1))
    return values[idx]


def summarize_route(samples: Iterable[RouteSample]) -> RouteTelemetry:
    items = tuple(samples)
    if not items:
        raise ValueError("empty_samples")
    route_ids = {s.route_id for s in items}
    if len(route_ids) != 1 or any(not s.route_id.strip() for s in items):
        raise ValueError("mixed_or_invalid_route")
    if any(s.latency_ms < 0 or s.context_tokens < 0 for s in items):
        raise ValueError("invalid_sample")
    latencies = [s.latency_ms for s in items]
    n = len(items)
    return RouteTelemetry(
        route_id=items[0].route_id,
        sample_count=n,
        p50_ms=_percentile(latencies, .50),
        p95_ms=_percentile(latencies, .95),
        error_rate=sum(not s.success for s in items) / n,
        cache_hit_rate=sum(s.cache_hit for s in items) / n,
        mean_context_tokens=sum(s.context_tokens for s in items) / n,
    )
