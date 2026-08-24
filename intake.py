from __future__ import annotations

from dataclasses import dataclass

from policy import PolicyDecision, decide_action
from projects import ProjectPolicy, get_project


@dataclass(frozen=True)
class IntakeDecision:
    project: ProjectPolicy
    policy: PolicyDecision
    disposition: str
    missing_evidence: tuple[str, ...]


def evaluate_event(project_id: str, payload: dict) -> IntakeDecision:
    project = get_project(project_id)
    requested_action = str(payload.get("requested_action", "classify"))
    policy = decide_action(requested_action)
    present = {key for key, value in payload.items() if value not in (None, "", [], {})}
    missing = tuple(key for key in project.next_evidence if key not in present)

    if requested_action in project.forbidden_actions:
        disposition = "forbidden_by_project_policy"
    elif project.status == "hold" and requested_action not in {"read", "classify", "summarize"}:
        disposition = "hold_project"
    elif policy.disposition in {"approval_required", "deny"}:
        disposition = policy.disposition
    elif missing:
        disposition = "continue_evidence_collection"
    else:
        disposition = "ready_for_analysis"
    return IntakeDecision(project, policy, disposition, missing)

