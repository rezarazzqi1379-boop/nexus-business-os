from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Decision = Literal["REJECT", "DRAFT_SKILL", "EXPERIMENT"]


@dataclass(frozen=True)
class SkillProposal:
    skill_id: str
    source_trajectory_ids: tuple[str, ...]
    project_scope: tuple[str, ...]
    instruction: str
    acceptance_tests: tuple[str, ...]
    rollback_ref: str
    requires_external_action: bool = False
    requires_production_access: bool = False

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        if not self.skill_id.strip():
            errors.append("skill_id required")
        if len(self.source_trajectory_ids) < 3:
            errors.append("at least three clean source trajectories required")
        if not self.project_scope:
            errors.append("project_scope required")
        if not self.instruction.strip():
            errors.append("instruction required")
        if not self.acceptance_tests:
            errors.append("acceptance_tests required")
        if not self.rollback_ref.strip():
            errors.append("rollback_ref required")
        return tuple(errors)


def decide_skill_proposal(p: SkillProposal) -> Decision:
    if p.validate():
        return "REJECT"
    if p.requires_external_action or p.requires_production_access:
        return "DRAFT_SKILL"
    return "EXPERIMENT"
