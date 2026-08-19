import pytest

from nexus_core.capacity_guard import Workload, CapacityBudget, plan_capacity


def test_overflow_delegates_background_work():
    budget = CapacityBudget(max_tokens=100, max_calls=2, max_latency_ms=1000, max_parallel=1)
    workloads = [
        Workload("interactive", "interactive", 50, 1, 100, 1, False, False),
        Workload("research", "research", 200, 3, 5000, 2, True, True),
    ]
    plan = plan_capacity(workloads, budget)
    assert plan.immediate == ("interactive",)
    assert plan.delegated == ("research",)
    assert "research" in plan.cache_candidates


def test_external_overflow_is_not_silently_delegated():
    budget = CapacityBudget(10, 1, 10, 0)
    item = Workload("send", "external", 1, 1, 1, 1, False, True)
    plan = plan_capacity([item], budget)
    assert plan.deferred == ("send",)
    assert not plan.delegated


def test_duplicate_work_id_fails_closed():
    budget = CapacityBudget(10, 10, 10, 10)
    w = Workload("x", "batch", 1, 1, 1, 1, False, True)
    with pytest.raises(ValueError):
        plan_capacity([w, w], budget)
