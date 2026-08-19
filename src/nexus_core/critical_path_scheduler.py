from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TaskNode:
    task_id: str
    depends_on: tuple[str, ...]
    estimated_latency_ms: int
    priority: int
    runnable: bool = True


@dataclass(frozen=True)
class WavePlan:
    waves: tuple[tuple[str, ...], ...]
    blocked: tuple[str, ...]
    estimated_critical_path_ms: int


def schedule_waves(nodes: Iterable[TaskNode], *, max_parallel: int = 4) -> WavePlan:
    if max_parallel < 1:
        raise ValueError("invalid_parallelism")
    items = tuple(nodes)
    by_id = {n.task_id: n for n in items}
    if len(by_id) != len(items) or any(not n.task_id.strip() for n in items):
        raise ValueError("invalid_or_duplicate_task")
    for n in items:
        if n.estimated_latency_ms < 0:
            raise ValueError("invalid_latency")
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
