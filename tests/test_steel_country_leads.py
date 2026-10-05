from datetime import date
import steel_country_leads as m
def base():
 return {"lead_id":"TR-001","country":"Turkey","company":"Example","role":"END_USER","applications":["gear"],"grade_candidates":["20MnCr5"],"evidence":[],"status":"DISCOVERED"}
def test_tier_a_without_evidence_rejected():
 r=base();r["tier"]="A";assert "tier_a_requires_current_evidence" in m.validate_lead(r)
def test_undated_evidence_cannot_support_tier_a():
 r=base();r["tier"]="A";r["evidence"]=[{"type":"OFFICIAL_COMPANY","ref":"https://example.com"}]
 e=m.validate_lead(r);assert "evidence_date_required:0" in e and "tier_a_requires_current_evidence" in e
def test_future_evidence_rejected(monkeypatch):
 r=base();r["evidence"]=[{"type":"OFFICIAL_COMPANY","ref":"https://example.com","observed_at":"2999-01-01"}]
 assert "invalid_evidence_date:0" in m.validate_lead(r)
def test_sensitive_transaction_fail_closed():
 r=base();r["country"]="Belarus";r["transaction_ready"]=True
 assert "sensitive_market_transaction_not_cleared" in m.validate_lead(r)

def test_fresh_claim_alone_cannot_support_tier_a():
 r=base();r["tier"]="A";r["evidence"]=[{"type":"CLAIM","ref":"claim:1","observed_at":"2026-10-05"}]
 e=m.validate_lead(r,today=date(2026,10,5))
 assert "tier_a_requires_qualifying_evidence" in e
def test_fresh_official_evidence_can_support_tier_a():
 r=base();r["tier"]="A";r["evidence"]=[{"type":"OFFICIAL_COMPANY","ref":"official:1","observed_at":"2026-10-05"}]
 e=m.validate_lead(r,today=date(2026,10,5))
 assert "tier_a_requires_current_evidence" not in e
 assert "tier_a_requires_qualifying_evidence" not in e
