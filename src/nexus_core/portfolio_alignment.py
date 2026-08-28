from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ProjectState = Literal[
    "ACTIVE_QUALIFICATION",
    "PAUSED_BY_MANAGEMENT",
    "COMMERCIAL_REFRESH_HOLD",
    "ENGINEERING_CLARIFICATION",
]
Decision = Literal["ALLOW_INTERNAL", "REFRESH_FIRST", "HOLD", "BLOCK_DUPLICATE_OUTREACH"]


@dataclass(frozen=True)
class ProjectControl:
    project_id: str
    state: ProjectState
    dynamic_unknowns: tuple[str, ...] = ()
    duplicate_outreach_blocked: bool = False


CANONICAL_PROJECT_CONTROLS: tuple[ProjectControl, ...] = (
    ProjectControl("PRJ-HYD-01", "ACTIVE_QUALIFICATION", duplicate_outreach_blocked=True),
    ProjectControl(
        "PRJ-KCL-01",
        "COMMERCIAL_REFRESH_HOLD",
        (
            "quantity_forecast",
            "permit_owner",
            "destination",
            "incoterm",
            "target_price",
            "payment_route",
            "sanctions_logistics_feasibility",
        ),
    ),
    ProjectControl("PRJ-HTL-01", "PAUSED_BY_MANAGEMENT", ("throughput_revalidation",)),
    ProjectControl(
        "PRJ-CAN-01",
        "ENGINEERING_CLARIFICATION",
        ("final_geometry", "mandatory_operations", "production_rate"),
    ),
)


def get_project_control(project_id: str) -> ProjectControl:
    matches = [item for item in CANONICAL_PROJECT_CONTROLS if item.project_id == project_id]
    if len(matches) != 1:
        raise ValueError(f"unknown or duplicate project control: {project_id}")
    return matches[0]


def gate_work(project_id: str, *, consequential: bool, is_follow_up: bool = False) -> Decision:
    control = get_project_control(project_id)
    if control.state == "PAUSED_BY_MANAGEMENT":
        return "HOLD"
    if control.duplicate_outreach_blocked and is_follow_up:
        return "BLOCK_DUPLICATE_OUTREACH"
    if consequential and control.dynamic_unknowns:
        return "REFRESH_FIRST"
    return "ALLOW_INTERNAL"
