from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

IdeaState = Literal["DISCOVERED", "VALIDATE", "EXPERIMENT", "WATCH", "DEFER", "REJECT"]
IdeaDomain = Literal["COMMERCIAL", "ENGINEERING", "AI_INFRA", "AUTOMATION", "PRODUCT", "DATA", "SECURITY", "DESIGN"]


@dataclass(frozen=True)
class IdeaCandidate:
    idea_id: str
    title: str
    domain: IdeaDomain
    problem: str
    evidence_refs: tuple[str, ...]
    project_refs: tuple[str, ...]
    expected_value: int
    strategic_fit: int
    time_to_evidence: int
    capital_intensity: int
    execution_difficulty: int
    risk: int
    evidence_quality: int
    reversibility: int
    acceptance_test: str
    rollback: str
    revisit_triggers: tuple[str, ...] = ()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for name in ("idea_id", "title", "problem", "acceptance_test", "rollback"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")
        for name in (
            "expected_value", "strategic_fit", "time_to_evidence", "capital_intensity",
            "execution_difficulty", "risk", "evidence_quality", "reversibility"
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or not 0 <= value <= 5:
                errors.append(f"{name} must be integer 0..5")
        if not self.evidence_refs:
            errors.append("at least one evidence_ref is required")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            errors.append("duplicate evidence_refs")
        if len(set(self.project_refs)) != len(self.project_refs):
            errors.append("duplicate project_refs")
        return tuple(errors)


@dataclass(frozen=True)
class IdeaDecision:
    state: IdeaState
    score: int
    reasons: tuple[str, ...]


def idea_score(item: IdeaCandidate) -> int:
    """Deterministic priority signal, never a probability."""
    errors = item.validate()
    if errors:
        raise ValueError("invalid idea: " + "; ".join(errors))
    return (
        4 * item.expected_value
        + 3 * item.strategic_fit
        + 3 * item.evidence_quality
        + 2 * item.reversibility
        + 2 * item.time_to_evidence
        - 2 * item.capital_intensity
        - 2 * item.execution_difficulty
        - 3 * item.risk
    )


def decide_idea(item: IdeaCandidate) -> IdeaDecision:
    errors = item.validate()
    if errors:
        return IdeaDecision("REJECT", -999, errors)
    score = idea_score(item)
    if item.risk >= 5 and item.evidence_quality <= 1:
        return IdeaDecision("REJECT", score, ("high risk with weak evidence",))
    if item.evidence_quality <= 1:
        return IdeaDecision("VALIDATE", score, ("evidence too weak for experiment",))
    if item.capital_intensity >= 4 and item.time_to_evidence <= 1:
        return IdeaDecision("WATCH", score, ("capital-heavy before fast validation",))
    if score >= 24 and item.reversibility >= 3:
        return IdeaDecision("EXPERIMENT", score, ("high-value reversible experiment candidate",))
    if score >= 12:
        return IdeaDecision("VALIDATE", score, ("promising but needs stronger proof",))
    return IdeaDecision("DEFER", score, ("preserve candidate; revisit when trigger or evidence improves",))


def rank_ideas(items: Sequence[IdeaCandidate]) -> tuple[IdeaCandidate, ...]:
    seen: set[str] = set()
    for item in items:
        if item.idea_id in seen:
            raise ValueError(f"duplicate idea_id: {item.idea_id}")
        seen.add(item.idea_id)
        if item.validate():
            raise ValueError(f"invalid idea {item.idea_id}: {'; '.join(item.validate())}")
    return tuple(sorted(items, key=lambda x: (-idea_score(x), x.idea_id)))
