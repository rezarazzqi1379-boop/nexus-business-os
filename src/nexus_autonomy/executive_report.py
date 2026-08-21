from dataclasses import dataclass

from nexus_autonomy.closed_loop import ClosedLoopResult


@dataclass(frozen=True)
class ExecutiveReport:
    completed: tuple[str, ...]
    failed: tuple[str, ...]
    approvals_required: tuple[str, ...]
    blocked: tuple[str, ...]
    deferred: tuple[str, ...]
    new_opportunities: tuple[str, ...]

    @property
    def needs_human_attention(self) -> bool:
        return bool(self.approvals_required or self.failed)


def build_executive_report(result: ClosedLoopResult) -> ExecutiveReport:
    """Compress a closed-loop cycle into decision-relevant information only."""
    if not isinstance(result, ClosedLoopResult):
        raise TypeError("result must be a ClosedLoopResult")

    completed: list[str] = []
    failed: list[str] = []
    for record in result.cycle.report.executed:
        if record.status == "succeeded":
            completed.append(record.task_id)
        elif record.status == "failed":
            failed.append(record.task_id)

    return ExecutiveReport(
        completed=tuple(completed),
        failed=tuple(failed),
        approvals_required=result.cycle.report.awaiting_approval_task_ids,
        blocked=result.cycle.report.blocked_task_ids,
        deferred=result.cycle.report.deferred_task_ids,
        new_opportunities=tuple(item.task_id for item in result.next_work),
    )
