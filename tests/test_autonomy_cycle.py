from pathlib import Path

from nexus_autonomy.cycle import run_stateful_cycle
from nexus_autonomy.run_state import FileRunnerStateStore
from nexus_autonomy.runner import ExecutionResult
from nexus_core.autonomy import AutonomyPlan, PlannedWork, WorkItem
from nexus_core.policy import evaluate_action, ActionIntent


def _work(task_id: str) -> PlannedWork:
    task = WorkItem(
        task_id=task_id,
        domain="research",
        objective=f"Research {task_id}",
        action_kind="research",
        acceptable_capability_ids=("web",),
        evidence_refs=("source:seed",),
        value="high",
        urgency="high",
        evidence="partial",
        cost="low",
    )
    gate = evaluate_action(
        ActionIntent(
            action_id=f"autonomy:{task_id}",
            kind="research",
            description=task.objective,
            reversible=True,
        )
    )
    return PlannedWork(task, "runnable", ("web",), (), gate)


def _plan(*task_ids: str) -> AutonomyPlan:
    return AutonomyPlan(
        runnable=tuple(_work(task_id) for task_id in task_ids),
        human_gated=(),
        blocked=(),
    )


def test_second_cycle_skips_successfully_completed_task(tmp_path: Path) -> None:
    store = FileRunnerStateStore(tmp_path / "runner-state.json")
    calls: list[str] = []

    def executor(item: PlannedWork) -> ExecutionResult:
        calls.append(item.task.task_id)
        return ExecutionResult("succeeded", "done", (f"evidence:{item.task.task_id}",))

    first = run_stateful_cycle(_plan("task-1"), {"research": executor}, store)
    second = run_stateful_cycle(_plan("task-1"), {"research": executor}, store)

    assert calls == ["task-1"]
    assert first.state_after.completed_task_ids == ("task-1",)
    assert second.report.executed[0].status == "skipped"
    assert second.state_after == first.state_after


def test_failed_task_is_retried_on_later_cycle(tmp_path: Path) -> None:
    store = FileRunnerStateStore(tmp_path / "runner-state.json")
    attempts = 0

    def executor(_: PlannedWork) -> ExecutionResult:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return ExecutionResult("failed", "temporary failure")
        return ExecutionResult("succeeded", "recovered", ("evidence:recovered",))

    first = run_stateful_cycle(_plan("task-1"), {"research": executor}, store)
    second = run_stateful_cycle(_plan("task-1"), {"research": executor}, store)

    assert first.state_after.completed_task_ids == ()
    assert second.state_after.completed_task_ids == ("task-1",)
    assert second.state_after.outcomes[0].attempts == 2


def test_action_budget_defers_without_marking_complete(tmp_path: Path) -> None:
    store = FileRunnerStateStore(tmp_path / "runner-state.json")

    def executor(item: PlannedWork) -> ExecutionResult:
        return ExecutionResult("succeeded", f"done {item.task.task_id}")

    result = run_stateful_cycle(
        _plan("task-1", "task-2"),
        {"research": executor},
        store,
        max_actions=1,
    )

    assert result.state_after.completed_task_ids == ("task-1",)
    assert result.report.deferred_task_ids == ("task-2",)
