from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Literal

EvidenceStrength = Literal["strong", "partial", "weak", "unverified"]
PathType = Literal["direct", "warm", "public", "none"]
NetworkRole = Literal["buyer", "supplier", "oem", "integrator", "epc", "trader", "intermediary", "referral", "owner", "unknown"]
_ALLOWED_EVIDENCE = {"strong", "partial", "weak", "unverified"}
_ALLOWED_PATHS = {"direct", "warm", "public", "none"}
_ALLOWED_ROLES = {"buyer", "supplier", "oem", "integrator", "epc", "trader", "intermediary", "referral", "owner", "unknown"}


@dataclass(frozen=True)
class CommercialCandidate:
    candidate_id: str; company_name: str; market: str
    product_fit: tuple[str, ...]; need_signals: tuple[str, ...]; role_signals: tuple[str, ...]
    contact_paths: tuple[str, ...]; evidence_refs: tuple[str, ...]
    evidence_strength: EvidenceStrength = "unverified"; path_type: PathType = "none"; duplicate_of: str | None = None
    network_roles: tuple[NetworkRole, ...] = ()
    future_themes: tuple[str, ...] = ()


@dataclass(frozen=True)
class QualifiedCandidate:
    candidate: CommercialCandidate; score: int
    state: Literal["qualified", "research_more", "reserve", "reject"]; reasons: tuple[str, ...]


def _valid_refs(values: object, *, allow_empty: bool = True) -> bool:
    return isinstance(values, tuple) and (allow_empty or bool(values)) and all(isinstance(v, str) and v.strip() for v in values) and len(values) == len(set(values))


def validate_commercial_candidate(item: CommercialCandidate) -> tuple[str, ...]:
    errors: list[str] = []
    for name, value in (("candidate_id", item.candidate_id), ("company_name", item.company_name), ("market", item.market)):
        if not isinstance(value, str) or not value.strip(): errors.append(f"invalid_{name}")
    for name, values in (("product_fit", item.product_fit), ("need_signals", item.need_signals), ("role_signals", item.role_signals), ("contact_paths", item.contact_paths), ("future_themes", item.future_themes)):
        if not _valid_refs(values): errors.append(f"invalid_{name}")
    if not _valid_refs(item.network_roles) or any(role not in _ALLOWED_ROLES for role in item.network_roles): errors.append("invalid_network_roles")
    if not _valid_refs(item.evidence_refs, allow_empty=False): errors.append("missing_evidence_refs" if not item.evidence_refs else "invalid_evidence_refs")
    if item.evidence_strength not in _ALLOWED_EVIDENCE: errors.append("invalid_evidence_strength")
    if item.path_type not in _ALLOWED_PATHS: errors.append("invalid_path_type")
    if item.duplicate_of is not None and (not isinstance(item.duplicate_of, str) or not item.duplicate_of.strip()): errors.append("invalid_duplicate_of")
    return tuple(errors)


def qualify_commercial_network(candidates: Iterable[CommercialCandidate]) -> tuple[QualifiedCandidate, ...]:
    """Rank current opportunities while preserving evidence-backed future network capital.

    A company can be worth retaining even when it is not a current opportunity. Reserve
    is deliberately separate from qualified/research_more so future-facing intermediaries,
    EPCs, owners and referral nodes are not discarded or falsely counted as pipeline.
    """
    results: list[QualifiedCandidate] = []; seen_ids: set[str] = set()
    for item in candidates:
        errors = validate_commercial_candidate(item)
        if errors: results.append(QualifiedCandidate(item, 0, "reject", errors)); continue
        if item.candidate_id in seen_ids: results.append(QualifiedCandidate(item, 0, "reject", ("duplicate_candidate_id",))); continue
        seen_ids.add(item.candidate_id)
        if item.duplicate_of: results.append(QualifiedCandidate(item, 0, "reject", ("duplicate_candidate",))); continue

        score = 0; reasons: list[str] = []
        if item.product_fit: score += min(30, 10 * len(item.product_fit)); reasons.append("product_fit")
        if item.need_signals: score += min(30, 10 * len(item.need_signals)); reasons.append("need_signal")
        if item.role_signals: score += min(20, 10 * len(item.role_signals)); reasons.append("relevant_role")
        if item.contact_paths: score += 10; reasons.append("contact_path")
        if item.network_roles: score += 5; reasons.append("network_role")
        if item.future_themes: score += 5; reasons.append("future_theme")
        verified_relationship_path = item.evidence_strength in {"strong", "partial"} and item.path_type in {"direct", "warm"}
        if verified_relationship_path: score += 10; reasons.append("verified_direct_or_warm_path")
        if item.evidence_strength == "strong": score += 10
        elif item.evidence_strength == "partial": score += 5
        elif item.evidence_strength == "unverified": score -= 15; reasons.append("unverified_evidence")

        hard_qualified = bool(item.product_fit and item.need_signals and item.role_signals and item.contact_paths)
        future_network_value = bool(item.network_roles or item.future_themes) and bool(item.contact_paths) and item.evidence_strength in {"strong", "partial", "weak"}
        if hard_qualified and verified_relationship_path:
            state = "qualified"
        elif item.evidence_strength == "unverified":
            state = "reject"
        elif item.product_fit or item.need_signals or item.role_signals:
            state = "research_more"
        elif future_network_value:
            state = "reserve"; reasons.append("future_network_reserve")
        else:
            state = "reject"
        results.append(QualifiedCandidate(item, max(0, score), state, tuple(reasons)))
    return tuple(sorted(results, key=lambda x: (-x.score, x.candidate.company_name.casefold(), x.candidate.candidate_id)))
