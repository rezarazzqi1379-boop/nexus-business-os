import pytest
from freelance_vertical_proof import EvidencePacket, DealEvent, prove_sandbox, deal_rhythm
from opportunity_qualification import OpportunityAssessment

def packet(**kw):
    d=dict(project_id="SANDBOX",source_locator="fixture:one",evidence_digest="sha256:abc",
           buyer_id="buyer",provider_id="provider",service_scope="engineering",
           need_observed_at="2026-10-10T00:00:00Z",identity_reviewed=True,demand_verified=True)
    d.update(kw)
    return EvidencePacket(**d)

def assessment():
    return OpportunityAssessment("opp-1","EXACT_FIT",evidence_quality=.9,recency=.9,
                                 logistics=.9,payment=.9,compliance=.9,deadline_feasibility=.9)

def test_untrusted_source_review_flags_do_not_promote():
    x=prove_sandbox(packet(),assessment(),opportunity_id="opp-1",as_of="2026-10-13T00:00:00Z")
    assert x["status"]=="RESEARCH_ONLY" and x["deal_stage"]=="PROSPECT"
    assert x["external_action_authorized"] is False

def test_stale_source_blocked():
    x=prove_sandbox(packet(need_observed_at="2026-01-01T00:00:00Z"),assessment(),
                    opportunity_id="opp-1",as_of="2026-10-13T00:00:00Z")
    assert x["reason"]=="stale_or_future_need"

def test_future_source_blocked():
    x=prove_sandbox(packet(need_observed_at="2026-10-14T00:00:00Z"),assessment(),
                    opportunity_id="opp-1",as_of="2026-10-13T00:00:00Z")
    assert x["reason"]=="stale_or_future_need"

def test_missing_locator_blocked():
    x=prove_sandbox(packet(source_locator=""),assessment(),
                    opportunity_id="opp-1",as_of="2026-10-13T00:00:00Z")
    assert x["reason"]=="invalid_source_provenance"

def test_observed_rhythm_is_deterministic():
    events=(DealEvent("opp","buyer","PROSPECT","2026-10-10T00:00:00Z","a"),
            DealEvent("opp","buyer","QUALIFIED","2026-10-11T12:00:00Z","b"))
    x=deal_rhythm(events)
    assert x["intervals"][0]["elapsed_seconds"]==129600
    assert x["conversion_rate"] is None and x["repeat_client_rate"] is None

def test_cross_client_events_rejected():
    events=(DealEvent("opp","a","PROSPECT","2026-10-10T00:00:00Z","a"),
            DealEvent("opp","b","QUALIFIED","2026-10-11T00:00:00Z","b"))
    with pytest.raises(ValueError,match="cross_client_events"):
        deal_rhythm(events)

def test_duplicate_events_rejected():
    e=DealEvent("opp","a","PROSPECT","2026-10-10T00:00:00Z","a")
    with pytest.raises(ValueError,match="duplicate_event"):
        deal_rhythm((e,e))

def test_naive_time_rejected():
    with pytest.raises(ValueError,match="timezone_required"):
        deal_rhythm((DealEvent("opp","a","PROSPECT","2026-10-10T00:00:00","a"),))

from commercial_chain_graph import candidate_edge

def _review():
    edge = candidate_edge(source_id="provider", relation="OFFERS_SERVICE_TO",
                          target_id="buyer", evidence_refs=("e1", "e2"),
                          source_families=("official", "independent"))
    receipt = dict(decision="APPROVED", project_id="SANDBOX",
                   source_id="provider", target_id="buyer",
                   relation="OFFERS_SERVICE_TO",
                   evidence_digests=("sha256:e1", "sha256:e2"),
                   reviewer_id="reviewer", receipt_id="receipt",
                   opportunity_id="opp-1", evidence_digest="sha256:abc",
                   need_observed_at="2026-10-10T00:00:00Z", need_verified=True)
    return edge, receipt

def test_trusted_review_promotes_to_human_review_not_outreach():
    edge, receipt = _review()
    x = prove_sandbox(packet(), assessment(), opportunity_id="opp-1",
                      as_of="2026-10-13T00:00:00Z",
                      trusted_review=receipt, reviewed_edge=edge)
    assert x["status"] == "HUMAN_REVIEW"
    assert x["external_action_authorized"] is False
    assert x["deal_stage"] == "PROSPECT"

def test_review_for_different_opportunity_fails_closed():
    edge, receipt = _review()
    receipt["opportunity_id"] = "opp-other"
    x = prove_sandbox(packet(), assessment(), opportunity_id="opp-1",
                      as_of="2026-10-13T00:00:00Z",
                      trusted_review=receipt, reviewed_edge=edge)
    assert x["status"] == "RESEARCH_ONLY"

def test_review_for_different_need_digest_fails_closed():
    edge, receipt = _review()
    receipt["evidence_digest"] = "sha256:other"
    x = prove_sandbox(packet(), assessment(), opportunity_id="opp-1",
                      as_of="2026-10-13T00:00:00Z",
                      trusted_review=receipt, reviewed_edge=edge)
    assert x["status"] == "RESEARCH_ONLY"

def test_review_without_verified_need_fails_closed():
    edge, receipt = _review()
    receipt["need_verified"] = False
    x = prove_sandbox(packet(), assessment(), opportunity_id="opp-1",
                      as_of="2026-10-13T00:00:00Z",
                      trusted_review=receipt, reviewed_edge=edge)
    assert x["status"] == "RESEARCH_ONLY"
