from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


SignalLevel = Literal["strong", "partial", "weak", "unverified"]
ReadinessBand = Literal["deal_ready", "quote_ready", "conversation_ready", "research_only", "blocked"]

_SIGNAL_WEIGHT = {"strong": 1.0, "partial": 0.65, "weak": 0.3, "unverified": 0.0}


@dataclass(frozen=True)
class CommercialCandidate:
    candidate_id: str
    company_name: str
    fit: SignalLevel
    need: SignalLevel
    decision_path: SignalLevel
    contact_path: SignalLevel
    responsiveness: SignalLevel
    technical_readiness: SignalLevel
    commercial_readiness: SignalLevel
    compliance_readiness: SignalLevel
    risk_penalty: float = 0.0
    evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CommercialForecast:
    candidate_id: str
    score: float
    band: ReadinessBand
    blockers: tuple[str, ...]
    next_best_action: str


def _validate(candidate: CommercialCandidate) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(candidate.candidate_id, str) or not candidate.candidate_id.strip():
        errors.append("candidate_id is required")
    if not isinstance(candidate.company_name, str) or not candidate.company_name.strip():
        errors.append("company_name is required")
    for name in (
        "fit", "need", "decision_path", "contact_path", "responsiveness",
        "technical_readiness", "commercial_readiness", "compliance_readiness",
    ):
        value = getattr(candidate, name)
        if value not in _SIGNAL_WEIGHT:
            errors.append(f"{name} is invalid")
    if not isinstance(candidate.risk_penalty, (int, float)) or not 0 <= candidate.risk_penalty <= 1:
        errors.append("risk_penalty must be between 0 and 1")
    if not isinstance(candidate.evidence_refs, tuple) or not candidate.evidence_refs:
        errors.append("evidence_refs are required")
    elif len(set(candidate.evidence_refs)) != len(candidate.evidence_refs):
        errors.append("evidence_refs cannot contain duplicates")
    return tuple(errors)


def forecast_candidate(candidate: CommercialCandidate) -> CommercialForecast:
    """Estimate commercial readiness without pretending prediction is certainty.

    The score is a prioritization heuristic, not a probability of closing. Missing
    technical/commercial/compliance evidence is surfaced as a blocker rather than
    hidden inside one aggregate number.
    """
    errors = _validate(candidate)
    if errors:
        return CommercialForecast(candidate.candidate_id, 0.0, "blocked", errors, "repair evidence/state before action")

    weighted = (
        1.3 * _SIGNAL_WEIGHT[candidate.fit]
        + 1.3 * _SIGNAL_WEIGHT[candidate.need]
        + 1.0 * _SIGNAL_WEIGHT[candidate.decision_path]
        + 1.0 * _SIGNAL_WEIGHT[candidate.contact_path]
        + 0.9 * _SIGNAL_WEIGHT[candidate.responsiveness]
        + 1.2 * _SIGNAL_WEIGHT[candidate.technical_readiness]
        + 1.2 * _SIGNAL_WEIGHT[candidate.commercial_readiness]
        + 1.1 * _SIGNAL_WEIGHT[candidate.compliance_readiness]
    )
    max_weight = 9.0
    score = max(0.0, min(100.0, (weighted / max_weight) * 100.0 - candidate.risk_penalty * 30.0))

    blockers: list[str] = []
    if candidate.need in ("weak", "unverified"): blockers.append("need not proven")
    if candidate.decision_path in ("weak", "unverified"): blockers.append("decision/referral path incomplete")
    if candidate.contact_path in ("weak", "unverified"): blockers.append("contact path incomplete")
    if candidate.technical_readiness in ("weak", "unverified"): blockers.append("technical requirements incomplete")
    if candidate.commercial_readiness in ("weak", "unverified"): blockers.append("commercial terms incomplete")
    if candidate.compliance_readiness in ("weak", "unverified"): blockers.append("compliance unresolved")

    if score >= 82 and not blockers:
        band: ReadinessBand = "deal_ready"
        next_action = "prepare Deal Decision Packet"
    elif score >= 68 and all(b not in blockers for b in ("technical requirements incomplete", "commercial terms incomplete")):
        band = "quote_ready"
        next_action = "request/compare quote and negotiate non-binding terms"
    elif score >= 48 and candidate.contact_path in ("strong", "partial"):
        band = "conversation_ready"
        next_action = "advance qualified conversation/clarification"
    else:
        band = "research_only"
        next_action = "resolve highest-value evidence gap before outreach"

    return CommercialForecast(candidate.candidate_id, round(score, 2), band, tuple(blockers), next_action)


def rank_candidates(candidates: Sequence[CommercialCandidate]) -> tuple[CommercialForecast, ...]:
    forecasts = [forecast_candidate(c) for c in candidates]
    return tuple(sorted(forecasts, key=lambda f: (-f.score, f.candidate_id)))
