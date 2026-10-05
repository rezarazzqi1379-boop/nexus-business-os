from steel_buyer_scoring import BuyerEvidence, score_buyer

REF=("source:verified",)

def test_generic_named_company_is_not_tier_a():
    s=score_buyer(BuyerEvidence(named_company=True))
    assert s.classification=="TIER_C" and s.buyer_fit<45

def test_evidence_rich_end_user_reaches_tier_a():
    s=score_buyer(BuyerEvidence(named_company=True,official_application_evidence=True,
      official_material_evidence=True,independent_trade_evidence=True,dimension_fit=True,end_user=True,
      application_refs=REF,material_refs=REF,trade_refs=REF,dimension_refs=REF))
    assert s.classification=="TIER_A" and s.buyer_fit==100

def test_unreferenced_positive_claims_do_not_inflate_score():
    s=score_buyer(BuyerEvidence(named_company=True,official_application_evidence=True,
      official_material_evidence=True,independent_trade_evidence=True,dimension_fit=True,end_user=True))
    assert s.classification=="TIER_C"
    assert "material_evidence_ref_required" in s.blockers

def test_compliance_is_separate_from_commercial_fit():
    s=score_buyer(BuyerEvidence(named_company=True,official_application_evidence=True,
      official_material_evidence=True,independent_trade_evidence=True,dimension_fit=True,end_user=True,
      application_refs=REF,material_refs=REF,trade_refs=REF,dimension_refs=REF,
      compliance_required=True,compliance_cleared=False))
    assert s.classification=="TIER_A"
    assert "compliance_clearance_required" in s.blockers
