from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

EvidenceStrength = Literal["strong", "partial", "weak", "unverified"]
PathType = Literal["direct", "warm", "public", "none"]


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


def qualify_commercial_network(candidates: Iterable[CommercialCandidate]) -> tuple[QualifiedCandidate, ...]:
    """Rank commercial paths without treating names or contact data as opportunity proof."""
    results: list[QualifiedCandidate] = []
    for item in candidates:
        if not item.candidate_id.strip() or not item.company_name.strip() or not item.evidence_refs:
            results.append(QualifiedCandidate(item, 0, "reject", ("missing_identity_or_evidence",)))
            continue
        if item.duplicate_of:
            results.append(QualifiedCandidate(item, 0, "reject", ("duplicate_candidate",)))
            continue
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
        elif score >= 25:
            state = "research_more"
        else:
            state = "reject"
        results.append(QualifiedCandidate(item, max(0, score), state, tuple(reasons)))
    return tuple(sorted(results, key=lambda x: (-x.score, x.candidate.company_name.casefold(), x.candidate.candidate_id)))
