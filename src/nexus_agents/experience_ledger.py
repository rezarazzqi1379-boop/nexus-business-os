from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Outcome = Literal["SUCCESS", "PARTIAL", "FAILURE", "UNKNOWN"]


@dataclass(frozen=True)
class ExperienceTrajectory:
    trajectory_id: str
    agent_id: str
    project_id: str
    task_id: str
    source_refs: tuple[str, ...]
    actions: tuple[str, ...]
    tests: tuple[str, ...]
    outcome: Outcome
    human_corrections: int
    reusable_lessons: tuple[str, ...]
    provenance_hash: str

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("trajectory_id", "agent_id", "project_id", "task_id", "provenance_hash"):
            if not getattr(self, name).strip():
                errors.append(f"{name} required")
        if self.human_corrections < 0:
            errors.append("human_corrections must be non-negative")
        if not self.tests:
            errors.append("tests required before trajectory can teach")
        if self.outcome == "UNKNOWN" and self.reusable_lessons:
            errors.append("unknown outcome cannot produce reusable lessons")
        return tuple(errors)


def eligible_for_learning(t: ExperienceTrajectory) -> bool:
    return not t.validate() and t.outcome == "SUCCESS" and t.human_corrections == 0
