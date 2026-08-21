from dataclasses import dataclass
from typing import Mapping

from nexus_autonomy.run_state import FileRunnerStateStore, RunnerState, apply_runner_report
from nexus_autonomy.runner import Executor, RunnerReport, run_autonomy_plan
from nexus_core.autonomy import AutonomyPlan


@dataclass(frozen=True)
class CycleResult:
    report: RunnerReport
    state_before: RunnerState
    state_after: RunnerState


def run_stateful_cycle(
    plan: AutonomyPlan,
    executors: Mapping[str, Executor],
    store: FileRunnerStateStore,
    *,
    max_actions: int = 10,
    stop_on_failure: bool = True,
) -> CycleResult:
    """Load durable state, run one bounded autonomy cycle, and persist its outcomes.

    Persistence happens only after the runner returns a structured report. A storage
    failure is surfaced to the caller rather than silently claiming durable progress.
    This function does not schedule itself and cannot authorize human-gated actions.
    """
    if not isinstance(store, FileRunnerStateStore):
        raise TypeError("store must be a FileRunnerStateStore")

    before = store.load()
    report = run_autonomy_plan(
        plan,
        executors,
        completed_task_ids=before.completed_task_ids,
        max_actions=max_actions,
        stop_on_failure=stop_on_failure,
    )
    after = apply_runner_report(before, report)
    store.save(after)
    return CycleResult(report=report, state_before=before, state_after=after)
