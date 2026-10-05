from steel_country_leads import validate_lead
def base():
 return {"lead_id":"TR-001","country":"Turkey","company":"Example","role":"END_USER",
 "applications":["gear"],"grade_candidates":["20MnCr5"],"evidence":[],"status":"DISCOVERED"}
def test_tier_a_without_evidence_rejected():
 r=base();r["tier"]="A";assert "tier_a_requires_evidence" in validate_lead(r)
def test_referenced_evidence_accepted():
 r=base();r["tier"]="A";r["evidence"]=[{"type":"OFFICIAL_COMPANY","ref":"https://example.com/materials"}]
 assert validate_lead(r)==()
def test_sensitive_transaction_fail_closed():
 r=base();r["country"]="Belarus";r["transaction_ready"]=True
 assert "sensitive_market_transaction_not_cleared" in validate_lead(r)
