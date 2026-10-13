"""NEXUS evidence hardening: content identity, freshness and claim-level evidence.

No external action authority is granted by this module.  It is intentionally
dependency-free so it can sit in front of durable intelligence ingestion.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
import json
from urllib.parse import urlsplit


class FreshnessClass(str, Enum):
    STATIC = "STATIC"
    SLOW_DYNAMIC = "SLOW_DYNAMIC"
    MEDIUM_DYNAMIC = "MEDIUM_DYNAMIC"
    FAST_DYNAMIC = "FAST_DYNAMIC"
    REALTIME_REQUIRED = "REALTIME_REQUIRED"


class ClaimRelation(str, Enum):
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    CONTEXTUALIZES = "CONTEXTUALIZES"


class ClaimState(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    SUPPORTED = "SUPPORTED"
    CONTRADICTED = "CONTRADICTED"
    STALE = "STALE"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True)
class EvidenceEnvelope:
    evidence_id: str
    project_id: str
    source_locator: str
    observed_at: str
    payload: object
    origin_id: str = ""
    lineage_roots: tuple[str, ...] = ()
    freshness_class: FreshnessClass = FreshnessClass.MEDIUM_DYNAMIC
    refresh_after: str = ""


@dataclass(frozen=True)
class ClaimEvidence:
    claim_id: str
    evidence_id: str
    project_id: str
    relation: ClaimRelation


def canonical_origin(e: EvidenceEnvelope) -> str:
    if e.origin_id.strip():
        return e.origin_id.strip().lower()
    source = e.source_locator.strip().lower()
    if "://" in source:
        return (urlsplit(source).hostname or source).removeprefix("www.")
    return source


def content_digest(payload: object) -> str:
    """Stable SHA-256 over canonical JSON-compatible content."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return sha256(encoded.encode("utf-8")).hexdigest()


def valid_envelope(e: EvidenceEnvelope) -> bool:
    if not all((e.evidence_id, e.project_id, e.source_locator, e.observed_at)):
        return False
    if e.refresh_after and e.refresh_after < e.observed_at:
        return False
    return True


def stale(e: EvidenceEnvelope, as_of: str) -> bool:
    if not valid_envelope(e):
        return True
    if e.freshness_class == FreshnessClass.STATIC:
        return False
    if not e.refresh_after:
        return True
    return as_of > e.refresh_after


def independent_lineage_roots(evidence: tuple[EvidenceEnvelope, ...], project_id: str) -> tuple[str, ...]:
    """Count source roots, never transport/search-result copies."""
    roots: set[str] = set()
    for item in evidence:
        if item.project_id != project_id or not valid_envelope(item):
            continue
        if item.lineage_roots:
            roots.update(r.strip().lower() for r in item.lineage_roots if r.strip())
        else:
            origin = canonical_origin(item)
            if origin:
                roots.add(origin)
    return tuple(sorted(roots))


def claim_state(
    claim_id: str,
    links: tuple[ClaimEvidence, ...],
    evidence: tuple[EvidenceEnvelope, ...],
    project_id: str,
    as_of: str,
) -> ClaimState:
    by_id = {e.evidence_id: e for e in evidence if e.project_id == project_id and valid_envelope(e)}
    relevant = tuple(
        link for link in links
        if link.claim_id == claim_id and link.project_id == project_id and link.evidence_id in by_id
    )
    if not relevant:
        return ClaimState.UNRESOLVED
    if any(stale(by_id[x.evidence_id], as_of) for x in relevant):
        return ClaimState.STALE
    supports = any(x.relation == ClaimRelation.SUPPORTS for x in relevant)
    refutes = any(x.relation == ClaimRelation.REFUTES for x in relevant)
    if supports and refutes:
        return ClaimState.NEEDS_REVIEW
    if refutes:
        return ClaimState.CONTRADICTED
    if supports:
        return ClaimState.SUPPORTED
    return ClaimState.UNRESOLVED
