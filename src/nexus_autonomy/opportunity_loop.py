from dataclasses import dataclass
from typing import Sequence

from nexus_core.autonomy import WorkItem


@dataclass(frozen=True)
class OpportunityCandidate:
    candidate_id: str
    objective: str
    evidence_refs: tuple[str, ...]
    domain: str = "market_intelligence"
    value: str = "medium"
    urgency: str = "medium"


def candidates_to_work_items(
    candidates: Sequence[OpportunityCandidate],
    *,
    acceptable_capability_ids: tuple[str, ...],
) -> tuple[WorkItem, ...]:
    """Convert discovered opportunities into research-only governed work.

    Discovery never grants outreach authority. Candidates become reversible research
    tasks first; any later external message must be a separate human-gated WorkItem.
    """
    if not acceptable_capability_ids:
        raise ValueError("acceptable_capability_ids requires at least one capability")

    work: list[WorkItem] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, OpportunityCandidate):
            raise TypeError("candidates must contain OpportunityCandidate values")
        if not candidate.candidate_id.strip() or not candidate.objective.strip():
            raise ValueError("candidate_id and objective are required")
        if candidate.candidate_id in seen:
            raise ValueError(f"duplicate candidate_id: {candidate.candidate_id}")
        seen.add(candidate.candidate_id)
        if not candidate.evidence_refs:
            raise ValueError("opportunity candidate requires retrievable evidence")
        work.append(
            WorkItem(
                task_id=f"opportunity:{candidate.candidate_id}",
                domain=candidate.domain,  # validated by WorkItem planner
                objective=candidate.objective,
                action_kind="research",
                acceptable_capability_ids=acceptable_capability_ids,
                evidence_refs=candidate.evidence_refs,
                value=candidate.value,
                urgency=candidate.urgency,
                evidence="partial",
                cost="low",
                write_required=False,
                reversible=True,
                goal_ref=f"opportunity:{candidate.candidate_id}",
                success_signal="produce evidence-backed qualification and next action",
                failure_signal="insufficient evidence, poor fit, or invalid opportunity",
            )
        )
    return tuple(work)
