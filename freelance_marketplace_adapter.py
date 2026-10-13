"""Sandbox-only freelance/commercial matching on existing NEXUS opportunity primitives.

This module ranks research candidates; it does not discover live demand, clear
compliance, authorize outreach, or turn a hypothesis into a verified deal.
"""
from dataclasses import dataclass
from opportunity_qualification import OpportunityAssessment, qualify
from deal_room import DealRoom, validate_deal_room

@dataclass(frozen=True)
class MarketplaceCandidate:
    opportunity_id: str
    project_id: str
    buyer_id: str
    provider_id: str
    service_scope: str
    evidence_refs: tuple[str, ...] = ()
    demand_verified: bool = False
    identity_reviewed: bool = False

@dataclass(frozen=True)
class MatchDecision:
    opportunity_id: str
    status: str
    reasons: tuple[str, ...]
    external_action_authorized: bool = False

def evaluate_match(candidate: MarketplaceCandidate, assessment: OpportunityAssessment) -> MatchDecision:
    """Fail closed; qualifying scores never override evidence and identity gates."""
    if not candidate.project_id.strip():
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", ("project_id_missing",))
    if not all((candidate.opportunity_id.strip(), candidate.buyer_id.strip(),
                candidate.provider_id.strip(), candidate.service_scope.strip())):
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", ("required_entity_missing",))
    if candidate.buyer_id == candidate.provider_id:
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", ("self_match",))
    if assessment.opportunity_id != candidate.opportunity_id:
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", ("assessment_scope_mismatch",))
    if not candidate.evidence_refs or len(set(candidate.evidence_refs)) != len(candidate.evidence_refs):
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", ("evidence_missing_or_duplicate",))
    if not candidate.identity_reviewed or not candidate.demand_verified:
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", ("identity_or_demand_unverified",))
    decision, reasons = qualify(assessment)
    if decision != "PURSUE":
        return MatchDecision(candidate.opportunity_id, "RESEARCH_ONLY", reasons or ("qualification_incomplete",))
    return MatchDecision(candidate.opportunity_id, "HUMAN_REVIEW", ("qualified_research_candidate",))

def draft_deal_room(candidate: MarketplaceCandidate) -> DealRoom:
    """A prospect record, not proof of contact or a transaction."""
    room = DealRoom(candidate.opportunity_id, "PROSPECT", candidate.evidence_refs,
                    next_action="Verify buyer identity, need, authority and project scope")
    assert not validate_deal_room(room)
    return room
