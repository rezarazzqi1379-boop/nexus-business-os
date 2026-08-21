from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from .evidence_authority import AuthorityTaggedHit, EvidenceAuthority, resolve_authority_contradiction
from .research_data_mesh import ResearchHit

PromotionAction = Literal["promote", "hold", "reject", "no_change"]


@dataclass(frozen=True)
class CanonicalClaim:
    project_id: str
    canonical_key: str
    value: str
    authority: EvidenceAuthority
    observed_at: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class CandidateClaim:
    project_id: str
    canonical_key: str
    value: str
    authority: EvidenceAuthority
    observed_at: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class PromotionDecision:
    action: PromotionAction
    reason: str
    requires_human_review: bool
    candidate_source_ids: tuple[str, ...]


def _bounded_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= 512


def _aware_iso(value: object) -> datetime | None:
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed.astimezone(timezone.utc)


def _validate_refs(refs: object) -> tuple[str, ...]:
    if not isinstance(refs, tuple) or not refs or any(not _bounded_text(ref) for ref in refs):
        raise ValueError("invalid_evidence_refs")
    if len(set(refs)) != len(refs):
        raise ValueError("duplicate_evidence_ref")
    return refs


def _validate_claim(claim: object, expected_type: type[CanonicalClaim] | type[CandidateClaim]) -> None:
    if not isinstance(claim, expected_type):
        raise ValueError("invalid_claim_type")
    if not all(_bounded_text(value) for value in (claim.project_id, claim.canonical_key, claim.value)):
        raise ValueError("invalid_claim_text")
    if _aware_iso(claim.observed_at) is None:
        raise ValueError("invalid_observed_at")
    _validate_refs(claim.evidence_refs)


def evaluate_state_promotion(current: CanonicalClaim, candidate: CandidateClaim) -> PromotionDecision:
    """Decide whether a candidate may change canonical state.

    The gate is intentionally conservative: cross-project writes fail closed; a candidate
    needs explicit provenance; equal-authority conflicting claims require human review;
    and stale evidence cannot replace an equal-authority canonical claim.
    """
    _validate_claim(current, CanonicalClaim)
    _validate_claim(candidate, CandidateClaim)

    if current.project_id != candidate.project_id:
        return PromotionDecision("reject", "cross_project_write", False, candidate.evidence_refs)
    if current.canonical_key != candidate.canonical_key:
        return PromotionDecision("reject", "canonical_key_mismatch", False, candidate.evidence_refs)

    current_time = _aware_iso(current.observed_at)
    candidate_time = _aware_iso(candidate.observed_at)
    assert current_time is not None and candidate_time is not None

    if current.value == candidate.value:
        if candidate_time <= current_time:
            return PromotionDecision("no_change", "same_value_not_fresher", False, candidate.evidence_refs)
        return PromotionDecision("no_change", "same_value_fresher_provenance", False, candidate.evidence_refs)

    current_hit = ResearchHit(
        "state-promotion",
        "canonical-current",
        current.canonical_key,
        current.canonical_key,
        current.value,
        "strong",
        100,
        "refute",
        independence_key="canonical-current",
    )
    candidate_hit = ResearchHit(
        "state-promotion",
        "candidate",
        candidate.canonical_key,
        candidate.canonical_key,
        candidate.value,
        "strong",
        100,
        "support",
        independence_key="candidate",
    )
    resolution = resolve_authority_contradiction(
        (
            AuthorityTaggedHit(candidate_hit, candidate.authority),
            AuthorityTaggedHit(current_hit, current.authority),
        )
    )

    if resolution.resolution == "refute":
        return PromotionDecision("reject", "lower_authority_than_canonical", False, candidate.evidence_refs)
    if resolution.resolution == "unresolved":
        return PromotionDecision("hold", "equal_authority_conflict", True, candidate.evidence_refs)

    # Candidate has strictly higher authority. Freshness is still recorded, but a lower-
    # authority current claim must not permanently block a better authoritative correction.
    return PromotionDecision("promote", "higher_authority_candidate", False, candidate.evidence_refs)
