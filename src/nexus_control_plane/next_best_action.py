from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ActionCandidate:
    action_id: str
    project_id: str
    action_type: str
    evidence_readiness: float
    expected_value: float
    information_gain: float
    urgency: float
    reversibility: float
    risk: float
    cost: float
    dependency_ready: bool
    source_authority_ok: bool
    unresolved_contradictions: int
    prior_failures_consulted: bool
    human_gate_required: bool = False


@dataclass(frozen=True)
class RankedAction:
    candidate: ActionCandidate
    score: float
    blocked: bool
    reasons: tuple[str, ...]
    ranking_is_advisory: bool = True


def _clean(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _unit(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


def rank_next_best_actions(candidates: tuple[ActionCandidate, ...]) -> tuple[RankedAction, ...]:
    """Rank bounded candidate actions without creating execution authority.

    Scores are transparent heuristics, not calibrated probabilities or ROI forecasts.
    Hard evidence/authority/contradiction failures block the candidate regardless of score.
    """
    if not isinstance(candidates, tuple):
        raise TypeError("candidates must be a tuple")

    ranked: list[RankedAction] = []
    seen: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, ActionCandidate):
            raise ValueError("invalid action candidate")
        if not all(_clean(getattr(candidate, f)) for f in ("action_id", "project_id", "action_type")):
            raise ValueError("candidate identifiers must be clean text")
        if candidate.action_id in seen:
            raise ValueError("action_id values must be unique")
        seen.add(candidate.action_id)
        for field in ("evidence_readiness", "expected_value", "information_gain", "urgency", "reversibility", "risk", "cost"):
            if not _unit(getattr(candidate, field)):
                raise ValueError(f"{field} must be within [0, 1]")
        for field in ("dependency_ready", "source_authority_ok", "prior_failures_consulted", "human_gate_required"):
            if not isinstance(getattr(candidate, field), bool):
                raise ValueError(f"{field} must be boolean")
        if not isinstance(candidate.unresolved_contradictions, int) or isinstance(candidate.unresolved_contradictions, bool) or candidate.unresolved_contradictions < 0:
            raise ValueError("unresolved_contradictions must be a non-negative integer")

        reasons: list[str] = []
        blocked = False
        if not candidate.source_authority_ok:
            reasons.append("canonical source authority is unresolved")
            blocked = True
        if candidate.unresolved_contradictions > 0:
            reasons.append("unresolved contradictions block material action")
            blocked = True
        if not candidate.dependency_ready:
            reasons.append("dependency is not ready")
            blocked = True
        if not candidate.prior_failures_consulted:
            reasons.append("relevant prior failures have not been consulted")
            blocked = True

        # Heuristic prioritization only. Positive terms reward evidence, value, learning,
        # urgency and reversibility; risk/cost are explicit penalties.
        score = (
            0.25 * candidate.evidence_readiness
            + 0.20 * candidate.expected_value
            + 0.20 * candidate.information_gain
            + 0.15 * candidate.urgency
            + 0.10 * candidate.reversibility
            - 0.07 * candidate.risk
            - 0.03 * candidate.cost
        )
        if candidate.human_gate_required:
            reasons.append("human gate is required before execution")
        if not reasons:
            reasons.append("advisory ranking only; no execution authority")
        ranked.append(RankedAction(candidate, round(score, 6), blocked, tuple(reasons)))

    return tuple(sorted(ranked, key=lambda item: (item.blocked, -item.score, item.candidate.action_id)))
