from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .state_promotion import CanonicalClaim, CandidateClaim, PromotionDecision


@dataclass(frozen=True)
class StateMutationAudit:
    mutation_id: str
    recorded_at: str
    project_id: str
    canonical_key: str
    action: str
    reason: str
    previous_value: str
    candidate_value: str
    previous_authority: str
    candidate_authority: str
    previous_evidence_refs: tuple[str, ...]
    candidate_evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class RollbackPlan:
    allowed: bool
    reason: str
    restore_value: str | None
    restore_authority: str | None
    restore_evidence_refs: tuple[str, ...]


def _bounded_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and value == value.strip() and len(value) <= 512


def _aware_iso(value: object) -> bool:
    if not isinstance(value, str) or not value or value != value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def record_state_mutation(
    current: CanonicalClaim,
    candidate: CandidateClaim,
    decision: PromotionDecision,
    *,
    mutation_id: str,
    recorded_at: str,
) -> StateMutationAudit:
    if not _bounded_text(mutation_id):
        raise ValueError("invalid_mutation_id")
    if not _aware_iso(recorded_at):
        raise ValueError("invalid_recorded_at")
    if current.project_id != candidate.project_id or current.canonical_key != candidate.canonical_key:
        raise ValueError("audit_claim_mismatch")
    if decision.action == "promote" and current.value == candidate.value:
        raise ValueError("invalid_promote_without_change")
    return StateMutationAudit(
        mutation_id=mutation_id,
        recorded_at=recorded_at,
        project_id=current.project_id,
        canonical_key=current.canonical_key,
        action=decision.action,
        reason=decision.reason,
        previous_value=current.value,
        candidate_value=candidate.value,
        previous_authority=current.authority,
        candidate_authority=candidate.authority,
        previous_evidence_refs=current.evidence_refs,
        candidate_evidence_refs=candidate.evidence_refs,
    )


def build_rollback_plan(audit: StateMutationAudit) -> RollbackPlan:
    if not isinstance(audit, StateMutationAudit):
        raise ValueError("invalid_audit")
    if audit.action != "promote":
        return RollbackPlan(False, "mutation_not_applied", None, None, ())
    return RollbackPlan(
        True,
        "restore_previous_canonical_snapshot",
        audit.previous_value,
        audit.previous_authority,
        audit.previous_evidence_refs,
    )
