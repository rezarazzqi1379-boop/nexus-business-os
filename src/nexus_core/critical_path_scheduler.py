from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Mapping

from nexus_core.latency_telemetry import RouteTelemetry


@dataclass(frozen=True)
class TaskNode:
    task_id: str
    depends_on: tuple[str, ...]
    estimated_latency_ms: int
    priority: int
    runnable: bool = True
    route_id: str | None = None


@dataclass(frozen=True)
class WavePlan:
    waves: tuple[tuple[str, ...], ...]
    blocked: tuple[str, ...]
    estimated_critical_path_ms: int


def _effective_nodes(
    nodes: Iterable[TaskNode],
    telemetry: Mapping[str, RouteTelemetry] | None,
    *,
    minimum_samples: int,
) -> tuple[TaskNode, ...]:
    items = tuple(nodes)
    if telemetry is None:
        return items
    if minimum_samples < 1:
        raise ValueError("invalid_minimum_samples")
    effective: list[TaskNode] = []
    for node in items:
        if node.route_id is None:
            effective.append(node)
            continue
        observed = telemetry.get(node.route_id)
        if observed is None or observed.sample_count < minimum_samples:
            effective.append(node)
            continue
        if observed.route_id != node.route_id:
            raise ValueError("telemetry_route_mismatch")
        effective.append(replace(node, estimated_latency_ms=observed.p95_ms))
    return tuple(effective)


def schedule_waves(
    nodes: Iterable[TaskNode],
    *,
    max_parallel: int = 4,
    telemetry: Mapping[str, RouteTelemetry] | None = None,
    minimum_samples: int = 5,
) -> WavePlan:
    if max_parallel < 1:
        raise ValueError("invalid_parallelism")
    items = _effective_nodes(nodes, telemetry, minimum_samples=minimum_samples)
    by_id = {n.task_id: n for n in items}
    if len(by_id) != len(items) or any(not n.task_id.strip() for n in items):
        raise ValueError("invalid_or_duplicate_task")
    for n in items:
        if n.estimated_latency_ms < 0:
            raise ValueError("invalid_latency")
        if n.route_id is not None and not n.route_id.strip():
            raise ValueError("invalid_route_id")
        if n.task_id in n.depends_on:
            raise ValueError("self_dependency")
        if len(set(n.depends_on)) != len(n.depends_on):
            raise ValueError("duplicate_dependency")

    missing = {d for n in items for d in n.depends_on if d not in by_id}
    blocked = {n.task_id for n in items if not n.runnable or any(d in missing for d in n.depends_on)}
    completed: set[str] = set()
    pending = {n.task_id for n in items if n.task_id not in blocked}
    waves: list[tuple[str, ...]] = []
    critical = 0

    while pending:
        ready = [by_id[i] for i in pending if set(by_id[i].depends_on) <= completed]
        if not ready:
            blocked.update(pending)
            break
        ready.sort(key=lambda n: (n.priority, -n.estimated_latency_ms, n.task_id))
        wave_nodes = ready[:max_parallel]
        wave = tuple(n.task_id for n in wave_nodes)
        waves.append(wave)
        critical += max((n.estimated_latency_ms for n in wave_nodes), default=0)
        completed.update(wave)
        pending.difference_update(wave)

    return WavePlan(tuple(waves), tuple(sorted(blocked)), critical)
