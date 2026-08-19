from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

WorkClass = Literal["interactive", "background", "batch", "research", "analysis", "external"]


@dataclass(frozen=True)
class Workload:
    work_id: str
    work_class: WorkClass
    estimated_tokens: int
    estimated_calls: int
    estimated_latency_ms: int
    priority: int
    cacheable: bool
    delegable: bool


@dataclass(frozen=True)
class CapacityBudget:
    max_tokens: int
    max_calls: int
    max_latency_ms: int
    max_parallel: int


@dataclass(frozen=True)
class CapacityPlan:
    immediate: tuple[str, ...]
    delegated: tuple[str, ...]
    deferred: tuple[str, ...]
    cache_candidates: tuple[str, ...]


def plan_capacity(workloads: Iterable[Workload], budget: CapacityBudget) -> CapacityPlan:
    items = tuple(workloads)
    if min(budget.max_tokens, budget.max_calls, budget.max_latency_ms, budget.max_parallel) < 0:
        raise ValueError("invalid_budget")
    seen: set[str] = set()
    for item in items:
        if not item.work_id.strip() or item.work_id in seen:
            raise ValueError("invalid_or_duplicate_work_id")
        seen.add(item.work_id)
        if min(item.estimated_tokens, item.estimated_calls, item.estimated_latency_ms) < 0:
            raise ValueError("invalid_estimate")
    ranked = sorted(items, key=lambda w: (w.priority, w.estimated_latency_ms, w.work_id))
    tokens = calls = latency = 0
    immediate: list[str] = []
    delegated: list[str] = []
    deferred: list[str] = []
    cache: list[str] = []
    for item in ranked:
        if item.cacheable:
            cache.append(item.work_id)
        fits = (
            len(immediate) < budget.max_parallel
            and tokens + item.estimated_tokens <= budget.max_tokens
            and calls + item.estimated_calls <= budget.max_calls
            and latency + item.estimated_latency_ms <= budget.max_latency_ms
        )
        if fits:
            immediate.append(item.work_id)
            tokens += item.estimated_tokens
            calls += item.estimated_calls
            latency += item.estimated_latency_ms
        elif item.delegable and item.work_class in {"background", "batch", "research", "analysis"}:
            delegated.append(item.work_id)
        else:
            deferred.append(item.work_id)
    return CapacityPlan(tuple(immediate), tuple(delegated), tuple(deferred), tuple(cache))
