from __future__ import annotations

from dataclasses import dataclass

from nexus_control_plane.control_plane import ControlPlane, WorkState
from nexus_control_plane.next_best_action import ActionCandidate, RankedAction, rank_next_best_actions


@dataclass(frozen=True)
class PortfolioSelection:
    selected_work_id: str | None
    ranked: tuple[RankedAction, ...]
    reasons: tuple[str, ...]


def select_next_ready_work(
    control_plane: ControlPlane,
    candidates: tuple[ActionCandidate, ...],
) -> PortfolioSelection:
    """Choose the highest-ranked READY work item without routing or executing it.

    Candidate action_id must equal an existing WorkItem.id. REVIEW/BLOCKED/RUNNING/DONE/
    REJECTED work cannot be selected even if its heuristic score is higher. Selection is
    advisory only; the caller must still invoke the existing routing and approval paths.
    """
    if not isinstance(control_plane, ControlPlane):
        raise TypeError("control_plane must be ControlPlane")
    ranked = rank_next_best_actions(candidates)
    reasons: list[str] = []

    for item in ranked:
        work = control_plane.work.get(item.candidate.action_id)
        if work is None:
            reasons.append(f"{item.candidate.action_id}: no matching work item")
            continue
        if work.project_id != item.candidate.project_id:
            reasons.append(f"{item.candidate.action_id}: project mismatch")
            continue
        if item.blocked:
            reasons.append(f"{item.candidate.action_id}: NBA blocked")
            continue
        if work.state is not WorkState.READY:
            reasons.append(f"{item.candidate.action_id}: work state is {work.state.value}, not ready")
            continue
        reasons.append(f"selected {work.id}: highest-ranked unblocked READY item")
        return PortfolioSelection(work.id, ranked, tuple(reasons))

    reasons.append("no unblocked READY work item is selectable")
    return PortfolioSelection(None, ranked, tuple(reasons))
