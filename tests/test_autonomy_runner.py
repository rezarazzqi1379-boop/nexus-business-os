from nexus_autonomy.runner import ExecutionResult, run_autonomy_plan
from nexus_core.autonomy import AutonomyPlan, PlannedWork, WorkItem
from nexus_core.policy import GateDecision


def _work(task_id: str, domain: str = "research") -> PlannedWork:
    task = WorkItem(
        task_id=task_id,
        domain=domain,
        objective=f"execute {task_id}",
        action_kind="research",
        acceptable_capability_ids=("web",),
        evidence_refs=(f"evidence:{task_id}",),
    )
    return PlannedWork(task, "runnable", ("web",), (), GateDecision(True, False, "ok"))


def test_runner_executes_only_runnable_and_surfaces_other_queues():
    runnable = _work("r1")
    gated = PlannedWork(runnable.task, "human_gate", (), ("approval",), GateDecision(False, True, "approval"))
    blocked = PlannedWork(runnable.task, "blocked", (), ("blocked",), GateDecision(False, False, "blocked"))
    plan = AutonomyPlan((runnable,), (gated,), (blocked,))

    report = run_autonomy_plan(
        plan,
        {"research": lambda _: ExecutionResult("succeeded", "done", ("result:1",))},
    )

    assert [record.task_id for record in report.executed] == ["r1"]
    assert report.awaiting_approval_task_ids == ("r1",)
    assert report.blocked_task_ids == ("r1",)


def test_runner_never_executes_human_gated_work():
    item = _work("send-1")
    gated = PlannedWork(item.task, "human_gate", (), ("approval",), GateDecision(False, True, "approval"))
    calls = []
    report = run_autonomy_plan(
        AutonomyPlan((), (gated,), ()),
        {"research": lambda work: calls.append(work) or ExecutionResult("succeeded", "bad")},
    )
    assert calls == []
    assert report.awaiting_approval_task_ids == ("send-1",)


def test_runner_respects_action_budget():
    plan = AutonomyPlan((_work("a"), _work("b"), _work("c")), (), ())
    report = run_autonomy_plan(
        plan,
        {"research": lambda work: ExecutionResult("succeeded", work.task.task_id)},
        max_actions=2,
    )
    assert [record.task_id for record in report.executed] == ["a", "b"]
    assert report.deferred_task_ids == ("c",)


def test_runner_stops_after_failure_by_default():
    plan = AutonomyPlan((_work("a"), _work("b")), (), ())
    report = run_autonomy_plan(
        plan,
        {"research": lambda _: ExecutionResult("failed", "source unavailable")},
    )
    assert report.executed[0].status == "failed"
    assert report.deferred_task_ids == ("b",)
    assert report.stopped_after_failure is True


def test_runner_missing_executor_fails_closed():
    report = run_autonomy_plan(AutonomyPlan((_work("a"),), (), ()), {})
    assert report.executed[0].status == "failed"
    assert "no executor registered" in report.executed[0].summary


def test_runner_skips_completed_task_ids():
    plan = AutonomyPlan((_work("a"), _work("b")), (), ())
    report = run_autonomy_plan(
        plan,
        {"research": lambda work: ExecutionResult("succeeded", work.task.task_id)},
        completed_task_ids=("a",),
        max_actions=1,
    )
    assert report.executed[0].status == "skipped"
    assert report.executed[1].task_id == "b"


def test_runner_contains_executor_exceptions():
    def explode(_):
        raise RuntimeError("boom")

    report = run_autonomy_plan(AutonomyPlan((_work("a"),), (), ()), {"research": explode})
    assert report.executed[0].status == "failed"
    assert "RuntimeError" in report.executed[0].summary
