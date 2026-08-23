from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class StateTransitionDecision(str, Enum):
    COMMIT = "commit"
    REJECT = "reject"
    HOLD = "hold"


@dataclass(frozen=True)
class StateTransitionRequest:
    transition_id: str
    prior_state_ref: str
    proposed_state_ref: str
    evidence_refs: tuple[str, ...]
    verifier_passed: bool
    invalidates_prior_verified_state: bool = False
    consequential: bool = False
    human_approved: bool = False


@dataclass(frozen=True)
class StateTransitionResult:
    decision: StateTransitionDecision
    reasons: tuple[str, ...]


def _clean(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def evaluate_state_transition(req: StateTransitionRequest) -> StateTransitionResult:
    """Commit state only through evidence-backed verified transitions.

    State is not mutated by planner confidence, worker consensus, or a self-reported
    completion claim. Consequential transitions also require the existing human gate.
    """
    if not isinstance(req, StateTransitionRequest):
        return StateTransitionResult(StateTransitionDecision.REJECT, ("invalid transition request",))

    reasons: list[str] = []
    for name in ("transition_id", "prior_state_ref", "proposed_state_ref"):
        if not _clean(getattr(req, name)):
            reasons.append(f"{name} is invalid")
    if not isinstance(req.evidence_refs, tuple) or not req.evidence_refs or any(not _clean(x) for x in req.evidence_refs):
        reasons.append("at least one valid evidence reference is required")
    elif len(set(req.evidence_refs)) != len(req.evidence_refs):
        reasons.append("evidence references must be unique")
    for field in ("verifier_passed", "invalidates_prior_verified_state", "consequential", "human_approved"):
        if not isinstance(getattr(req, field), bool):
            reasons.append(f"{field} must be boolean")

    if reasons:
        return StateTransitionResult(StateTransitionDecision.REJECT, tuple(reasons))
    if not req.verifier_passed:
        return StateTransitionResult(StateTransitionDecision.HOLD, ("verifier did not establish progress",))
    if req.invalidates_prior_verified_state:
        return StateTransitionResult(
            StateTransitionDecision.HOLD,
            ("transition invalidates previously verified state; contradiction/recovery review required",),
        )
    if req.consequential and not req.human_approved:
        return StateTransitionResult(StateTransitionDecision.HOLD, ("consequential transition requires human approval",))
    return StateTransitionResult(StateTransitionDecision.COMMIT, ("verified evidence-backed transition",))
