from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

LatencyClass = Literal["interactive", "soft_realtime", "delay_tolerant"]


@dataclass(frozen=True)
class SLO:
    route_id: str
    latency_class: LatencyClass
    p95_ms_target: int
    availability_target: float
    error_rate_max: float
    max_parallel: int


def validate_slo(slo: SLO) -> tuple[str, ...]:
    errors: list[str] = []
    if not slo.route_id.strip(): errors.append("invalid_route_id")
    if slo.p95_ms_target <= 0: errors.append("invalid_p95_target")
    if not 0 < slo.availability_target <= 1: errors.append("invalid_availability_target")
    if not 0 <= slo.error_rate_max < 1: errors.append("invalid_error_rate")
    if slo.max_parallel < 1: errors.append("invalid_parallelism")
    return tuple(errors)


def build_sla_registry(items: Iterable[SLO]) -> dict[str, SLO]:
    registry: dict[str, SLO] = {}
    for item in items:
        if validate_slo(item):
            raise ValueError("invalid_slo")
        if item.route_id in registry:
            raise ValueError("duplicate_route_id")
        registry[item.route_id] = item
    return registry
