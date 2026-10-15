from __future__ import annotations

from dataclasses import dataclass

from .workforce import CapabilitySpec, Department, catalog
from .workforce_orchestrator import WORKFLOW_TEMPLATES, WorkflowKind


@dataclass(frozen=True)
class MissionTeam:
    mission_id: str
    workflow_kind: WorkflowKind
    departments: tuple[Department, ...]
    capability_ids: tuple[str, ...]
    consequential_capability_ids: tuple[str, ...]


def build_mission_team(mission_id: str, workflow_kind: WorkflowKind) -> MissionTeam:
    if not mission_id or mission_id.strip() != mission_id:
        raise ValueError("mission_id must be canonical")
    if not isinstance(workflow_kind, WorkflowKind):
        raise ValueError("workflow_kind must be WorkflowKind")

    index: dict[str, CapabilitySpec] = {item.capability_id: item for item in catalog()}
    capability_ids: list[str] = []
    departments: list[Department] = []
    consequential: list[str] = []

    for step in WORKFLOW_TEMPLATES[workflow_kind]:
        capability = index[step.capability_id]
        if capability.capability_id not in capability_ids:
            capability_ids.append(capability.capability_id)
        if capability.department not in departments:
            departments.append(capability.department)
        if capability.requires_human_approval:
            consequential.append(capability.capability_id)

    if Department.NEXUS_CORE not in departments:
        departments.append(Department.NEXUS_CORE)

    return MissionTeam(
        mission_id=mission_id,
        workflow_kind=workflow_kind,
        departments=tuple(departments),
        capability_ids=tuple(capability_ids),
        consequential_capability_ids=tuple(consequential),
    )


def mission_team_is_minimal(team: MissionTeam) -> bool:
    """A mission team should contain exactly the capabilities required by its workflow template."""
    expected = tuple(dict.fromkeys(step.capability_id for step in WORKFLOW_TEMPLATES[team.workflow_kind]))
    return team.capability_ids == expected
