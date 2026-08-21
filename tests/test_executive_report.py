from nexus_autonomy.closed_loop import ClosedLoopResult
from nexus_autonomy.cycle import CycleResult
from nexus_autonomy.executive_report import build_executive_report
from nexus_autonomy.outcome_ledger import OutcomeLedger
from nexus_autonomy.run_state import RunnerState
from nexus_autonomy.runner import RunRecord, RunnerReport
from nexus_core.autonomy import WorkItem


def test_report_surfaces_only_decision_relevant_queues():
    cycle = CycleResult(
        report=RunnerReport(
            executed=(
                RunRecord("done", "succeeded", "ok", ()),
                RunRecord("bad", "failed", "nope", ()),
                RunRecord("old", "skipped", "already completed", ()),
            ),
            awaiting_approval_task_ids=("approve-1",),
            blocked_task_ids=("blocked-1",),
            deferred_task_ids=("later-1",),
            stopped_after_failure=True,
        ),
        state_before=RunnerState(),
        state_after=RunnerState(),
    )
    next_item = WorkItem(
        task_id="opportunity:new-1", domain="research", objective="qualify", action_kind="research",
        acceptable_capability_ids=("web",), evidence_refs=("ref",),
    )
    result = ClosedLoopResult(cycle=cycle, ledger=OutcomeLedger(), next_work=(next_item,))
    report = build_executive_report(result)
    assert report.completed == ("done",)
    assert report.failed == ("bad",)
    assert report.approvals_required == ("approve-1",)
    assert report.blocked == ("blocked-1",)
    assert report.deferred == ("later-1",)
    assert report.new_opportunities == ("opportunity:new-1",)
    assert report.needs_human_attention is True


def test_success_only_cycle_needs_no_human_attention():
    cycle = CycleResult(
        report=RunnerReport((RunRecord("done", "succeeded", "ok", ()),), (), (), (), False),
        state_before=RunnerState(), state_after=RunnerState(),
    )
    report = build_executive_report(ClosedLoopResult(cycle, OutcomeLedger(), ()))
    assert report.needs_human_attention is False
