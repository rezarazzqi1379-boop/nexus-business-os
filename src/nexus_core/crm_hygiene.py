from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


CRMCategory = Literal["commercial", "personal", "education", "finance", "noise", "unknown"]


@dataclass(frozen=True)
class CRMRecordCandidate:
    record_id: str
    record_type: Literal["contact", "company"]
    display_name: str
    email_or_domain: str | None
    category_hint: CRMCategory | None
    project_refs: tuple[str, ...]
    commercial_evidence_refs: tuple[str, ...]
    contact_path_refs: tuple[str, ...]
    excluded_reason: str | None = None


@dataclass(frozen=True)
class CRMClassification:
    record_id: str
    category: CRMCategory
    promote_to_commercial_pipeline: bool
    reason: str


def classify_crm_record(candidate: CRMRecordCandidate) -> CRMClassification:
    """Classify CRM records without promoting inbox noise into the deal pipeline.

    The classifier is intentionally conservative: commercial promotion requires an
    explicit commercial/project link plus retrievable commercial evidence. A contact
    merely existing in Gmail, HubSpot or an imported address book is not sufficient.
    """
    if not isinstance(candidate, CRMRecordCandidate):
        return CRMClassification("", "unknown", False, "invalid candidate type")
    if not candidate.record_id.strip() or not candidate.display_name.strip():
        return CRMClassification(candidate.record_id, "unknown", False, "missing stable identity")
    if candidate.excluded_reason:
        return CRMClassification(candidate.record_id, "noise", False, candidate.excluded_reason)

    hint = candidate.category_hint or "unknown"
    if hint in ("personal", "education", "finance", "noise"):
        return CRMClassification(candidate.record_id, hint, False, f"explicit category hint: {hint}")

    has_project = bool(candidate.project_refs)
    has_commercial_evidence = bool(candidate.commercial_evidence_refs)
    has_contact_path = bool(candidate.contact_path_refs)

    if has_project and has_commercial_evidence and has_contact_path:
        return CRMClassification(candidate.record_id, "commercial", True, "project + commercial evidence + contact path verified")
    if hint == "commercial" and not (has_project and has_commercial_evidence):
        return CRMClassification(candidate.record_id, "unknown", False, "commercial hint lacks project/evidence proof")
    return CRMClassification(candidate.record_id, "unknown", False, "insufficient evidence for commercial promotion")


def commercial_pipeline_candidates(candidates: Sequence[CRMRecordCandidate]) -> tuple[CRMRecordCandidate, ...]:
    """Return only unique evidence-complete commercial candidates."""
    retained: list[CRMRecordCandidate] = []
    seen_ids: set[str] = set()
    seen_addresses: set[str] = set()
    for candidate in candidates:
        if not isinstance(candidate, CRMRecordCandidate):
            continue
        if candidate.record_id in seen_ids:
            continue
        classification = classify_crm_record(candidate)
        if not classification.promote_to_commercial_pipeline:
            continue
        address = (candidate.email_or_domain or "").strip().casefold()
        if address and address in seen_addresses:
            continue
        seen_ids.add(candidate.record_id)
        if address:
            seen_addresses.add(address)
        retained.append(candidate)
    return tuple(retained)
