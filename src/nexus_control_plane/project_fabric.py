from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class ProjectDomain(str, Enum):
    PROCUREMENT = "procurement"
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    RESEARCH = "research"
    DESIGN = "design"
    OPERATIONS = "operations"


class ProjectState(str, Enum):
    DISCOVERY = "discovery"
    ACTIVE = "active"
    WAITING = "waiting"
    BLOCKED = "blocked"
    REVIEW = "review"
    DONE = "done"


@dataclass(frozen=True)
class ProjectProfile:
    project_id: str
    domain: ProjectDomain
    state: ProjectState
    strategic_value: int
    urgency: int
    evidence_quality: float
    downside_risk: int
    human_attention_cost: int
    has_authoritative_requirements: bool
    has_measured_outcome: bool

    def validate(self) -> None:
        if not self.project_id or self.project_id.strip() != self.project_id:
            raise ValueError("project_id must be canonical")
        for value, name in (
            (self.strategic_value, "strategic_value"),
            (self.urgency, "urgency"),
            (self.downside_risk, "downside_risk"),
            (self.human_attention_cost, "human_attention_cost"),
        ):
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100")
        if not 0.0 <= self.evidence_quality <= 1.0:
            raise ValueError("evidence_quality must be between 0 and 1")


@dataclass(frozen=True)
class PortfolioDecision:
    project_id: str
    score: float
    action: str
    reasons: tuple[str, ...]


def _score(profile: ProjectProfile) -> float:
    evidence_bonus = 20 * profile.evidence_quality
    authority_bonus = 10 if profile.has_authoritative_requirements else 0
    outcome_bonus = 8 if profile.has_measured_outcome else 0
    return (
        0.34 * profile.strategic_value
        + 0.24 * profile.urgency
        + evidence_bonus
        + authority_bonus
        + outcome_bonus
        - 0.18 * profile.downside_risk
        - 0.12 * profile.human_attention_cost
    )


def coordinate_portfolio(projects: Iterable[ProjectProfile]) -> tuple[PortfolioDecision, ...]:
    profiles = tuple(projects)
    seen: set[str] = set()
    decisions: list[PortfolioDecision] = []
    for profile in profiles:
        profile.validate()
        if profile.project_id in seen:
            raise ValueError(f"duplicate project_id: {profile.project_id}")
        seen.add(profile.project_id)

        reasons: list[str] = []
        if profile.state is ProjectState.DONE:
            action = "archive_learn"
            reasons.append("project is done; preserve evidence and extract reusable lessons")
        elif profile.state is ProjectState.WAITING:
            action = "watch_no_duplicate_action"
            reasons.append("waiting state should be monitored without duplicate outreach")
        elif profile.state is ProjectState.BLOCKED:
            action = "resolve_blocker"
            reasons.append("resolve the current blocker before adding execution activity")
        elif not profile.has_authoritative_requirements and profile.domain in {ProjectDomain.PROCUREMENT, ProjectDomain.ENGINEERING}:
            action = "authority_first"
            reasons.append("decision-critical requirements lack authoritative confirmation")
        elif profile.evidence_quality < 0.45:
            action = "research_first"
            reasons.append("evidence quality is too low for reliable execution")
        elif profile.has_measured_outcome:
            action = "optimize"
            reasons.append("measured outcomes exist; prioritize improvement against baseline")
        else:
            action = "execute_measure"
            reasons.append("execute the next safe step and capture an outcome before further scaling")

        decisions.append(PortfolioDecision(profile.project_id, _score(profile), action, tuple(reasons)))

    return tuple(sorted(decisions, key=lambda item: (-item.score, item.project_id)))
