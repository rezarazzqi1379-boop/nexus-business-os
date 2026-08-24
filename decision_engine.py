from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class DecisionOption:
    option_id: str
    commercial_value: int
    strategic_fit: int
    evidence_strength: int
    time_sensitivity: int
    reversibility: int
    cost: int
    downside_risk: int
    blocked: bool = False


@dataclass(frozen=True)
class RankedOption:
    option_id: str
    score: int
    disposition: str


def _validate(item: DecisionOption) -> None:
    if not item.option_id.strip():
        raise ValueError("invalid_option_id")
    for value in (item.commercial_value, item.strategic_fit, item.evidence_strength,
                  item.time_sensitivity, item.reversibility, item.cost, item.downside_risk):
        if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 5:
            raise ValueError("invalid_option_score")


def rank_options(options: Iterable[DecisionOption]) -> tuple[RankedOption, ...]:
    """Deterministic triage; scores prioritize decisions, never replace human judgment."""
    items = tuple(options)
    seen: set[str] = set()
    ranked: list[RankedOption] = []
    for item in items:
        _validate(item)
        if item.option_id in seen:
            raise ValueError("duplicate_option_id")
        seen.add(item.option_id)
        score = (item.commercial_value * 4 + item.strategic_fit * 3 + item.evidence_strength * 4
                 + item.time_sensitivity * 2 + item.reversibility * 2 - item.cost * 2
                 - item.downside_risk * 4)
        if item.blocked:
            disposition = "blocked"
        elif item.evidence_strength < 2 or item.downside_risk >= 4:
            disposition = "collect_evidence_or_review"
        elif score >= 35:
            disposition = "candidate_next_action"
        else:
            disposition = "defer"
        ranked.append(RankedOption(item.option_id, score, disposition))
    return tuple(sorted(ranked, key=lambda x: (-x.score, x.option_id)))

