from nexus_autonomy.closed_loop import run_closed_loop_cycle
from nexus_autonomy.opportunity_loop import OpportunityCandidate
from nexus_autonomy.outcome_ledger import OutcomeLedger
from nexus_autonomy.run_state import FileRunnerStateStore
from nexus_autonomy.runner import ExecutionResult
from nexus_core.autonomy import AutonomyPlan, PlannedWork, WorkItem
from nexus_core.policy import GateDecision


def runnable(task_id="r1"):
    task = WorkItem(
        task_id=task_id,
        domain="research",
        objective="qualify opportunity",
        action_kind="research",
        acceptable_capability_ids=("web",),
        evidence_refs=("seed:1",),
    )
    return PlannedWork(task, "runnable", ("web",), (), GateDecision(True, False, "ok"))


def test_cycle_records_outcome_and_generates_research_only_next_work(tmp_path):
    plan = AutonomyPlan((runnable(),), (), ())
    store = FileRunnerStateStore(tmp_path / "state.json")

    result = run_closed_loop_cycle(
        cycle_id="c1",
        plan=plan,
        executors={"research": lambda _: ExecutionResult("succeeded", "qualified", ("evidence:1",))},
        state_store=store,
        ledger=OutcomeLedger(),
        candidate_producer=lambda cycle, ledger: (
            OpportunityCandidate("next-1", "Investigate next lead", ("evidence:1",)),
        ),
        discovery_capability_ids=("web",),
    )

    assert result.ledger.latest_for("r1").status == "succeeded"
    assert len(result.next_work) == 1
    assert result.next_work[0].action_kind == "research"
    assert result.next_work[0].write_required is False


def test_completed_task_is_not_reexecuted_on_next_cycle(tmp_path):
    plan = AutonomyPlan((runnable(),), (), ())
    store = FileRunnerStateStore(tmp_path / "state.json")
    calls = 0

    def execute(_):
        nonlocal calls
        calls += 1
        return ExecutionResult("succeeded", "done", ("evidence:1",))

    first = run_closed_loop_cycle(
        cycle_id="c1", plan=plan, executors={"research": execute}, state_store=store,
        ledger=OutcomeLedger(), candidate_producer=lambda *_: (), discovery_capability_ids=("web",),
    )
    second = run_closed_loop_cycle(
        cycle_id="c2", plan=plan, executors={"research": execute}, state_store=store,
        ledger=first.ledger, candidate_producer=lambda *_: (), discovery_capability_ids=("web",),
    )

    assert calls == 1
    assert second.cycle.report.executed[0].status == "skipped"
    assert len(second.ledger.events) == 1
