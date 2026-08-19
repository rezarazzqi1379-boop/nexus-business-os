from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from nexus_core.connector_broker import Capability, ConnectorRoute
from nexus_core.latency_telemetry import RouteTelemetry
from nexus_core.sla_registry import SLO


@dataclass(frozen=True)
class BoundConnectorSLA:
    route_id: str
    capable: bool
    healthy: bool
    has_slo: bool
    has_telemetry: bool
    sample_count: int
    within_p95: bool
    within_error_budget: bool
    meets_availability: bool
    compliant: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class SLARouteDecision:
    selected: str | None
    fallbacks: tuple[str, ...]
    blocked_reason: str | None


def bind_connector_slas(
    routes: Iterable[ConnectorRoute],
    *,
    required: Capability,
    sla_registry: dict[str, SLO],
    telemetry: Iterable[RouteTelemetry],
    minimum_samples: int = 5,
) -> tuple[BoundConnectorSLA, ...]:
    if minimum_samples < 1:
        raise ValueError("invalid_minimum_samples")

    telemetry_by_route: dict[str, RouteTelemetry] = {}
    for item in telemetry:
        if item.route_id in telemetry_by_route:
            raise ValueError("duplicate_telemetry_route")
        telemetry_by_route[item.route_id] = item

    seen: set[str] = set()
    bound: list[BoundConnectorSLA] = []
    for route in routes:
        if route.name in seen:
            raise ValueError("duplicate_route_name")
        seen.add(route.name)

        capable = required in route.capabilities
        healthy = route.health == "healthy"
        slo = sla_registry.get(route.name)
        sample = telemetry_by_route.get(route.name)
        reasons: list[str] = []

        if not capable:
            reasons.append("missing_required_capability")
        if not healthy:
            reasons.append("route_not_healthy")
        if slo is None:
            reasons.append("missing_slo")
        if sample is None:
            reasons.append("missing_telemetry")

        sample_count = sample.sample_count if sample is not None else 0
        within_p95 = bool(sample is not None and slo is not None and sample.p95_ms <= slo.p95_ms_target)
        within_error_budget = bool(sample is not None and slo is not None and sample.error_rate <= slo.error_rate_max)
        meets_availability = bool(sample is not None and slo is not None and (1.0 - sample.error_rate) >= slo.availability_target)

        if sample is not None and sample.sample_count < minimum_samples:
            reasons.append("insufficient_samples")
        if sample is not None and slo is not None:
            if not within_p95:
                reasons.append("p95_target_missed")
            if not within_error_budget:
                reasons.append("error_budget_exceeded")
            if not meets_availability:
                reasons.append("availability_target_missed")

        compliant = (
            capable
            and healthy
            and slo is not None
            and sample is not None
            and sample.sample_count >= minimum_samples
            and within_p95
            and within_error_budget
            and meets_availability
        )
        bound.append(
            BoundConnectorSLA(
                route_id=route.name,
                capable=capable,
                healthy=healthy,
                has_slo=slo is not None,
                has_telemetry=sample is not None,
                sample_count=sample_count,
                within_p95=within_p95,
                within_error_budget=within_error_budget,
                meets_availability=meets_availability,
                compliant=compliant,
                reasons=tuple(reasons),
            )
        )
    return tuple(bound)


def choose_sla_compliant_route(
    routes: Iterable[ConnectorRoute],
    *,
    required: Capability,
    sla_registry: dict[str, SLO],
    telemetry: Iterable[RouteTelemetry],
    minimum_samples: int = 5,
) -> SLARouteDecision:
    route_items = tuple(routes)
    bindings = bind_connector_slas(
        route_items,
        required=required,
        sla_registry=sla_registry,
        telemetry=telemetry,
        minimum_samples=minimum_samples,
    )
    compliant_ids = {item.route_id for item in bindings if item.compliant}
    eligible = [route for route in route_items if route.name in compliant_ids]
    if not eligible:
        return SLARouteDecision(None, (), "no_sla_compliant_route")
    eligible.sort(
        key=lambda r: (
            r.priority,
            -r.reliability_score,
            r.latency_ms if r.latency_ms is not None else 10**9,
            r.cost_score,
            r.name,
        )
    )
    return SLARouteDecision(eligible[0].name, tuple(r.name for r in eligible[1:]), None)
