from datetime import date
from steel_evidence_quality import canonical_domain,lead_identity,evidence_freshness
def test_domain_dedup_ignores_www():
 assert canonical_domain("https://www.Example.com/a")=="example.com"
 assert lead_identity("Turkey","Example A","https://www.example.com")==lead_identity("turkey","Other","https://example.com")
def test_freshness_is_deterministic():
 assert evidence_freshness("2026-01-01T00:00:00+00:00",max_age_days=30,today=date(2026,2,1))=="STALE"
 assert evidence_freshness("2026-01-20",max_age_days=30,today=date(2026,2,1))=="FRESH"
def test_future_evidence_rejected():
 assert evidence_freshness("2027-01-01",today=date(2026,2,1))=="INVALID_FUTURE"
