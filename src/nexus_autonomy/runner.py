from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence

from nexus_core.autonomy import AutonomyPlan, PlannedWork


RunStatus = Literal["succeeded", "failed", "skipped"]
Executor = Callable[[PlannedWork], "ExecutionResult"]


@dataclass(frozen=True)
class ExecutionResult:
    status: RunStatus
    summary: str
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunRecord:
    task_id: str
    status: RunStatus
    summary: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RunnerReport:
    executed: tuple[RunRecord, ...]
    awaiting_approval_task_ids: tuple[str, ...]
    blocked_task_ids: tuple[str, ...]
    deferred_task_ids: tuple[str, ...]
    stopped_after_failure: bool


def _validate_result(result: object) -> ExecutionResult:
    if not isinstance(result, ExecutionResult):
        raise TypeError("executor must return ExecutionResult")
    if result.status not in {"succeeded", "failed", "skipped"}:
        raise ValueError("executor returned unsupported status")
    if not isinstance(result.summary, str) or not result.summary.strip():
        raise ValueError("executor result summary is required")
    if not isinstance(result.evidence_refs, tuple):
        raise ValueError("executor evidence_refs must be a tuple")
    if any(not isinstance(ref, str) or not ref.strip() for ref in result.evidence_refs):
        raise ValueError("executor evidence_refs must contain nonblank strings")
    return result


def run_autonomy_plan(
    plan: AutonomyPlan,
    executors: Mapping[str, Executor],
    *,
    completed_task_ids: Sequence[str] = (),
    max_actions: int = 10,
    stop_on_failure: bool = True,
) -> RunnerReport:
    """Execute only work already classified runnable by the autonomy planner.

    This runner deliberately cannot approve gated work. It is a bounded execution
    loop, not an authorization layer. Missing executors fail closed. Completed task
    ids provide a simple idempotency boundary for callers with durable state.
    """
    if not isinstance(plan, AutonomyPlan):
        raise TypeError("plan must be an AutonomyPlan")
    if not isinstance(max_actions, int) or isinstance(max_actions, bool) or max_actions < 0:
        raise ValueError("max_actions must be a non-negative integer")
    if not isinstance(stop_on_failure, bool):
        raise ValueError("stop_on_failure must be a boolean")

    completed = set(completed_task_ids)
    if len(completed) != len(tuple(completed_task_ids)):
        raise ValueError("completed_task_ids cannot contain duplicates")
    if any(not isinstance(task_id, str) or not task_id.strip() for task_id in completed):
        raise ValueError("completed_task_ids must contain nonblank strings")

    executed: list[RunRecord] = []
    deferred: list[str] = []
    stopped = False

    runnable = list(plan.runnable)
    for index, item in enumerate(runnable):
        task_id = item.task.task_id
        if task_id in completed:
            executed.append(RunRecord(task_id, "skipped", "already completed", ()))
            continue
        if len([record for record in executed if record.status != "skipped"]) >= max_actions:
            deferred.extend(work.task.task_id for work in runnable[index:])
            break

        executor = executors.get(item.task.domain)
        if executor is None:
            result = ExecutionResult("failed", f"no executor registered for domain={item.task.domain}")
        else:
            try:
                result = _validate_result(executor(item))
            except Exception as exc:  # fail closed at the orchestration boundary
                result = ExecutionResult("failed", f"executor error: {type(exc).__name__}: {exc}")

        executed.append(RunRecord(task_id, result.status, result.summary, result.evidence_refs))
        if result.status == "failed" and stop_on_failure:
            deferred.extend(work.task.task_id for work in runnable[index + 1 :])
            stopped = True
            break

    return RunnerReport(
        executed=tuple(executed),
        awaiting_approval_task_ids=tuple(item.task.task_id for item in plan.human_gated),
        blocked_task_ids=tuple(item.task.task_id for item in plan.blocked),
        deferred_task_ids=tuple(deferred),
        stopped_after_failure=stopped,
    )
