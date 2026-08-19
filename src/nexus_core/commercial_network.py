from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

EvidenceStrength = Literal["strong", "partial", "weak", "unverified"]
PathType = Literal["direct", "warm", "public", "none"]
_ALLOWED_EVIDENCE = {"strong", "partial", "weak", "unverified"}
_ALLOWED_PATHS = {"direct", "warm", "public", "none"}


@dataclass(frozen=True)
class CommercialCandidate:
    candidate_id: str
    company_name: str
    market: str
    product_fit: tuple[str, ...]
    need_signals: tuple[str, ...]
    role_signals: tuple[str, ...]
    contact_paths: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    evidence_strength: EvidenceStrength = "unverified"
    path_type: PathType = "none"
    duplicate_of: str | None = None


@dataclass(frozen=True)
class QualifiedCandidate:
    candidate: CommercialCandidate
    score: int
    state: Literal["qualified", "research_more", "reject"]
    reasons: tuple[str, ...]


def _valid_refs(values: object, *, allow_empty: bool = True) -> bool:
    return isinstance(values, tuple) and (allow_empty or bool(values)) and all(isinstance(value, str) and value.strip() for value in values) and len(values) == len(set(values))


def validate_commercial_candidate(item: CommercialCandidate) -> tuple[str, ...]:
    errors: list[str] = []
    for name, value in (("candidate_id", item.candidate_id), ("company_name", item.company_name), ("market", item.market)):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"invalid_{name}")
    for name, values in (("product_fit", item.product_fit), ("need_signals", item.need_signals), ("role_signals", item.role_signals), ("contact_paths", item.contact_paths)):
        if not _valid_refs(values):
            errors.append(f"invalid_{name}")
    if not _valid_refs(item.evidence_refs, allow_empty=False):
        errors.append("missing_evidence_refs" if not item.evidence_refs else "invalid_evidence_refs")
    if item.evidence_strength not in _ALLOWED_EVIDENCE:
        errors.append("invalid_evidence_strength")
    if item.path_type not in _ALLOWED_PATHS:
        errors.append("invalid_path_type")
    if item.duplicate_of is not None and (not isinstance(item.duplicate_of, str) or not item.duplicate_of.strip()):
        errors.append("invalid_duplicate_of")
    return tuple(errors)


def qualify_commercial_network(candidates: Iterable[CommercialCandidate]) -> tuple[QualifiedCandidate, ...]:
    """Rank commercial paths without treating names or contact data as opportunity proof."""
    results: list[QualifiedCandidate] = []
    seen_ids: set[str] = set()
    for item in candidates:
        errors = validate_commercial_candidate(item)
        if errors:
            results.append(QualifiedCandidate(item, 0, "reject", errors)); continue
        if item.candidate_id in seen_ids:
            results.append(QualifiedCandidate(item, 0, "reject", ("duplicate_candidate_id",))); continue
        seen_ids.add(item.candidate_id)
        if item.duplicate_of:
            results.append(QualifiedCandidate(item, 0, "reject", ("duplicate_candidate",))); continue

        score = 0
        reasons: list[str] = []
        if item.product_fit:
            score += min(30, 10 * len(item.product_fit)); reasons.append("product_fit")
        if item.need_signals:
            score += min(30, 10 * len(item.need_signals)); reasons.append("need_signal")
        if item.role_signals:
            score += min(20, 10 * len(item.role_signals)); reasons.append("relevant_role")
        if item.contact_paths:
            score += 10; reasons.append("contact_path")
        if item.path_type in {"direct", "warm"}:
            score += 10; reasons.append("direct_or_warm_path")
        if item.evidence_strength == "strong":
            score += 10
        elif item.evidence_strength == "partial":
            score += 5
        elif item.evidence_strength == "unverified":
            score -= 15; reasons.append("unverified_evidence")

        hard_qualified = bool(item.product_fit and item.need_signals and item.role_signals and item.contact_paths)
        if hard_qualified and score >= 60 and item.evidence_strength in {"strong", "partial"}:
            state = "qualified"
        elif item.product_fit or item.need_signals or item.role_signals or item.contact_paths:
            state = "research_more"
        else:
            state = "reject"
        results.append(QualifiedCandidate(item, max(0, score), state, tuple(reasons)))
    return tuple(sorted(results, key=lambda x: (-x.score, x.candidate.company_name.casefold(), x.candidate.candidate_id)))
