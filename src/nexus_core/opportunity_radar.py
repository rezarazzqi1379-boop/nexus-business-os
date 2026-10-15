from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

OpportunityDecision = Literal["REJECT", "WATCH", "VALIDATE", "EXPERIMENT"]


@dataclass(frozen=True)
class OpportunityCandidate:
    opportunity_id: str
    title: str
    problem: str
    evidence_refs: tuple[str, ...]
    project_refs: tuple[str, ...]
    expected_value: int
    evidence_quality: int
    reversibility: int
    execution_difficulty: int
    capital_intensity: int
    safety_risk: int
    acceptance_test: str
    rollback: str
    duplicate_of: str | None = None

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("opportunity_id", "title", "problem", "acceptance_test", "rollback"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} required")
        for name in ("expected_value", "evidence_quality", "reversibility", "execution_difficulty", "capital_intensity", "safety_risk"):
            value = getattr(self, name)
            if not isinstance(value, int) or not 0 <= value <= 5:
                errors.append(f"{name} must be integer 0..5")
        if not self.evidence_refs:
            errors.append("evidence_refs required")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            errors.append("duplicate evidence_refs")
        if len(set(self.project_refs)) != len(self.project_refs):
            errors.append("duplicate project_refs")
        if self.duplicate_of == self.opportunity_id:
            errors.append("opportunity cannot duplicate itself")
        return tuple(errors)


def decide(candidate: OpportunityCandidate) -> OpportunityDecision:
    if candidate.validate() or candidate.duplicate_of:
        return "REJECT"
    if candidate.safety_risk >= 5:
        return "REJECT"
    if candidate.evidence_quality <= 1:
        return "WATCH"
    if candidate.capital_intensity >= 4 or candidate.execution_difficulty >= 4:
        return "VALIDATE"
    if candidate.expected_value >= 4 and candidate.reversibility >= 3 and candidate.safety_risk <= 3:
        return "EXPERIMENT"
    return "VALIDATE"


def score(candidate: OpportunityCandidate) -> int:
    if candidate.validate() or candidate.duplicate_of:
        return -100
    return (
        candidate.expected_value * 4
        + candidate.evidence_quality * 3
        + candidate.reversibility * 2
        - candidate.execution_difficulty * 2
        - candidate.capital_intensity * 2
        - candidate.safety_risk * 3
    )


def ranked(candidates: tuple[OpportunityCandidate, ...]) -> tuple[OpportunityCandidate, ...]:
    unique: dict[str, OpportunityCandidate] = {}
    for item in candidates:
        if item.opportunity_id in unique:
            raise ValueError(f"duplicate opportunity_id: {item.opportunity_id}")
        unique[item.opportunity_id] = item
    return tuple(sorted(candidates, key=lambda item: (score(item), item.opportunity_id), reverse=True))
