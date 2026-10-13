from freelance_marketplace_adapter import MarketplaceCandidate, evaluate_match, draft_deal_room
from opportunity_qualification import OpportunityAssessment

def candidate(**changes):
    d = dict(opportunity_id="synthetic-1", project_id="SANDBOX", buyer_id="buyer-a",
             provider_id="provider-b", service_scope="industrial design",
             evidence_refs=("synthetic:one",), demand_verified=True, identity_reviewed=True)
    d.update(changes)
    return MarketplaceCandidate(**d)

def assessment(**changes):
    d = dict(opportunity_id="synthetic-1", product_fit="EXACT_FIT",
             evidence_quality=.9, recency=.9, logistics=.9, payment=.9,
             compliance=.9, deadline_feasibility=.9)
    d.update(changes)
    return OpportunityAssessment(**d)

def test_review_ready_is_never_outreach_authority():
    x = evaluate_match(candidate(), assessment())
    assert x.status == "HUMAN_REVIEW"
    assert not x.external_action_authorized

def test_unverified_demand_blocks_high_score():
    assert evaluate_match(candidate(demand_verified=False), assessment()).status == "RESEARCH_ONLY"

def test_unreviewed_identity_blocks_high_score():
    assert evaluate_match(candidate(identity_reviewed=False), assessment()).status == "RESEARCH_ONLY"

def test_cross_opportunity_assessment_blocked():
    assert evaluate_match(candidate(), assessment(opportunity_id="synthetic-2")).status == "RESEARCH_ONLY"

def test_missing_project_id_blocked():
    assert evaluate_match(candidate(project_id=""), assessment()).status == "RESEARCH_ONLY"

def test_duplicate_evidence_blocked():
    assert evaluate_match(candidate(evidence_refs=("a", "a")), assessment()).status == "RESEARCH_ONLY"

def test_self_match_blocked():
    assert evaluate_match(candidate(provider_id="buyer-a"), assessment()).status == "RESEARCH_ONLY"

def test_unknown_compliance_blocks_promotion():
    assert evaluate_match(candidate(), assessment(compliance=None)).status == "RESEARCH_ONLY"

def test_draft_remains_prospect():
    x = draft_deal_room(candidate())
    assert x.stage == "PROSPECT" and x.next_action and not x.contacts
