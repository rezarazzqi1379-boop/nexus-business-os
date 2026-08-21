from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from nexus_autonomy.cycle import CycleResult, run_stateful_cycle
from nexus_autonomy.opportunity_loop import OpportunityCandidate, candidates_to_work_items
from nexus_autonomy.outcome_ledger import OutcomeLedger, append_report
from nexus_autonomy.run_state import FileRunnerStateStore
from nexus_autonomy.runner import Executor
from nexus_core.autonomy import AutonomyPlan, WorkItem

CandidateProducer = Callable[[CycleResult, OutcomeLedger], Sequence[OpportunityCandidate]]


@dataclass(frozen=True)
class ClosedLoopResult:
    cycle: CycleResult
    ledger: OutcomeLedger
    next_work: tuple[WorkItem, ...]


def run_closed_loop_cycle(
    *,
    cycle_id: str,
    plan: AutonomyPlan,
    executors: Mapping[str, Executor],
    state_store: FileRunnerStateStore,
    ledger: OutcomeLedger,
    candidate_producer: CandidateProducer,
    discovery_capability_ids: tuple[str, ...],
    max_actions: int = 10,
) -> ClosedLoopResult:
    """Execute one bounded cycle, record outcomes, then propose governed next work.

    The candidate producer sees structured outcomes but cannot directly execute anything.
    All generated opportunities are converted into research-only WorkItems and must pass
    the normal autonomy planner/capability/policy gates in a later cycle.
    """
    if not isinstance(cycle_id, str) or not cycle_id.strip():
        raise ValueError("cycle_id must be a nonblank string")
    if not isinstance(ledger, OutcomeLedger):
        raise TypeError("ledger must be an OutcomeLedger")
    if not callable(candidate_producer):
        raise TypeError("candidate_producer must be callable")

    cycle = run_stateful_cycle(
        plan,
        executors,
        state_store,
        max_actions=max_actions,
    )
    updated_ledger = append_report(ledger, cycle_id, cycle.report)
    candidates = tuple(candidate_producer(cycle, updated_ledger))
    next_work = candidates_to_work_items(
        candidates,
        acceptable_capability_ids=discovery_capability_ids,
    )
    return ClosedLoopResult(cycle=cycle, ledger=updated_ledger, next_work=next_work)
