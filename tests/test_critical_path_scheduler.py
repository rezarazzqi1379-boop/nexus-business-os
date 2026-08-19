import pytest

from nexus_core.critical_path_scheduler import TaskNode, schedule_waves


def test_independent_tasks_run_in_parallel_then_join():
    plan = schedule_waves([
        TaskNode("research", (), 500, 2),
        TaskNode("code", (), 800, 1),
        TaskNode("verify", ("research", "code"), 200, 1),
    ], max_parallel=2)
    assert set(plan.waves[0]) == {"research", "code"}
    assert plan.waves[1] == ("verify",)
    assert plan.estimated_critical_path_ms == 1000


def test_cycle_fails_closed_as_blocked():
    plan = schedule_waves([
        TaskNode("a", ("b",), 1, 1),
        TaskNode("b", ("a",), 1, 1),
    ])
    assert set(plan.blocked) == {"a", "b"}
    assert not plan.waves


def test_missing_dependency_blocks_task():
    plan = schedule_waves([TaskNode("a", ("missing",), 1, 1)])
    assert plan.blocked == ("a",)


def test_parallelism_is_bounded():
    nodes = [TaskNode(str(i), (), 1, i) for i in range(7)]
    plan = schedule_waves(nodes, max_parallel=3)
    assert all(len(wave) <= 3 for wave in plan.waves)


def test_duplicate_task_fails_closed():
    with pytest.raises(ValueError):
        schedule_waves([TaskNode("x", (), 1, 1), TaskNode("x", (), 1, 1)])
