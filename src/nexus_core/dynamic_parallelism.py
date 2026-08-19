from __future__ import annotations

from dataclasses import dataclass

from nexus_core.latency_telemetry import RouteTelemetry
from nexus_core.sla_registry import SLO


@dataclass(frozen=True)
class ParallelismDecision:
    route_id: str
    selected_parallelism: int
    reason: str


def choose_parallelism(
    telemetry: RouteTelemetry,
    slo: SLO,
    *,
    current_parallelism: int,
    minimum_samples: int = 5,
) -> ParallelismDecision:
    if telemetry.route_id != slo.route_id:
        raise ValueError("route_mismatch")
    if current_parallelism < 1:
        raise ValueError("invalid_current_parallelism")
    current = min(current_parallelism, slo.max_parallel)
    if telemetry.sample_count < minimum_samples:
        return ParallelismDecision(slo.route_id, current, "insufficient_samples_hold")
    if telemetry.error_rate > slo.error_rate_max:
        return ParallelismDecision(slo.route_id, max(1, current // 2), "error_budget_exceeded")
    if telemetry.p95_ms > slo.p95_ms_target:
        return ParallelismDecision(slo.route_id, max(1, current - 1), "p95_target_missed")
    if telemetry.p95_ms <= int(slo.p95_ms_target * .70) and current < slo.max_parallel:
        return ParallelismDecision(slo.route_id, current + 1, "healthy_headroom")
    return ParallelismDecision(slo.route_id, current, "within_slo_hold")
