"""Deterministic SANDBOX freelance vertical proof and observed deal-rhythm metrics.

No real demand, review-service authentication, outreach, or transaction authority.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from freelance_marketplace_adapter import MarketplaceCandidate, evaluate_match, draft_deal_room
from opportunity_qualification import OpportunityAssessment
from commercial_chain_graph import ChainEdge, promote_reviewed

@dataclass(frozen=True)
class EvidencePacket:
    project_id: str
    source_locator: str
    evidence_digest: str
    buyer_id: str
    provider_id: str
    service_scope: str
    need_observed_at: str
    identity_reviewed: bool = False
    demand_verified: bool = False

@dataclass(frozen=True)
class DealEvent:
    opportunity_id: str
    client_id: str
    stage: str
    occurred_at: str
    evidence_ref: str

def _timestamp(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timezone_required")
    return result.astimezone(timezone.utc)

def deal_rhythm(events: tuple[DealEvent, ...]) -> dict:
    """Compute only observed consecutive stage intervals; never infer outcomes."""
    ordered = sorted(events, key=lambda e: _timestamp(e.occurred_at))
    if len({e.opportunity_id for e in ordered}) > 1:
        raise ValueError("cross_opportunity_events")
    if len({e.client_id for e in ordered}) > 1:
        raise ValueError("cross_client_events")
    if any(not e.evidence_ref.strip() for e in ordered):
        raise ValueError("event_evidence_required")
    if len({(e.stage, e.occurred_at, e.evidence_ref) for e in ordered}) != len(ordered):
        raise ValueError("duplicate_event")
    intervals = tuple({
        "from_stage": left.stage, "to_stage": right.stage,
        "elapsed_seconds": int((_timestamp(right.occurred_at)-_timestamp(left.occurred_at)).total_seconds())
    } for left, right in zip(ordered, ordered[1:]))
    return {"observed_events": len(ordered), "intervals": intervals,
            "conversion_rate": None, "repeat_client_rate": None}

def prove_sandbox(packet: EvidencePacket, assessment: OpportunityAssessment,
                  *, opportunity_id: str, as_of: str, max_age_days: int = 30,
                  trusted_review: dict | None = None,
                  reviewed_edge: ChainEdge | None = None) -> dict:
    """Synthetic source-to-prospect proof. Source-provided review flags are not authority."""
    if not packet.project_id or not packet.source_locator or not packet.evidence_digest.startswith("sha256:"):
        return {"status": "RESEARCH_ONLY", "reason": "invalid_source_provenance"}
    try:
        age = (_timestamp(as_of) - _timestamp(packet.need_observed_at)).total_seconds()
    except (ValueError, TypeError):
        return {"status": "RESEARCH_ONLY", "reason": "invalid_timestamp"}
    if age < 0 or age > max_age_days * 86400:
        return {"status": "RESEARCH_ONLY", "reason": "stale_or_future_need"}
    review_ok = False
    if trusted_review is not None and reviewed_edge is not None:
        review_ok = (
            reviewed_edge.source_id == packet.provider_id
            and reviewed_edge.target_id == packet.buyer_id
            and reviewed_edge.relation == "OFFERS_SERVICE_TO"
            and trusted_review.get("opportunity_id") == opportunity_id
            and trusted_review.get("evidence_digest") == packet.evidence_digest
            and trusted_review.get("need_observed_at") == packet.need_observed_at
            and trusted_review.get("need_verified") is True
            and promote_reviewed(reviewed_edge, receipt=trusted_review,
                                project_id=packet.project_id,
                                evidence_digests=tuple(trusted_review.get("evidence_digests", ()))
                                ).state == "VERIFIED"
        )
    candidate = MarketplaceCandidate(opportunity_id, packet.project_id, packet.buyer_id,
                                     packet.provider_id, packet.service_scope,
                                     (packet.source_locator,), review_ok, review_ok)
    # A source packet may claim review/verification; it cannot authorize promotion.
    result = evaluate_match(candidate, assessment)
    room = draft_deal_room(candidate)
    return {"status": result.status, "reason": "trusted_review_passed" if review_ok else "trusted_review_required",
            "deal_stage": room.stage, "external_action_authorized": False,
            "evidence_digest": packet.evidence_digest}
