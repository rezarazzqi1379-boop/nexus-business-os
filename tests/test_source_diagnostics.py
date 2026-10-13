from commercial_source_registry import source_by_id
from source_diagnostics import *

def p(health=SourceHealth.HEALTHY,n=0):
 return SourceProbe("KZ-UNIFIED-PROC",health,"2026-10-07T00:00:00Z",returned_records=n)

def test_procurement_source_fits_procurement_question():
 assert question_fit(source_by_id("KZ-UNIFIED-PROC"),EvidenceQuestion.CURRENT_PROCUREMENT)

def test_trade_data_does_not_fit_company_procurement_question():
 assert not question_fit(source_by_id("GLOBAL-COMTRADE"),EvidenceQuestion.CURRENT_PROCUREMENT)
 assert question_fit(source_by_id("GLOBAL-COMTRADE"),EvidenceQuestion.MARKET_TRADE)

def test_supplier_route_does_not_fit_current_demand_question():
 assert not question_fit(source_by_id("OM-JSRS"),EvidenceQuestion.CURRENT_PROCUREMENT)
 assert question_fit(source_by_id("OM-JSRS"),EvidenceQuestion.SUPPLIER_ROUTE)

def test_healthy_empty_result_is_bounded_negative_evidence():
 s=negative_evidence_statement(source_by_id("KZ-UNIFIED-PROC"),p(),EvidenceQuestion.CURRENT_PROCUREMENT,"chain PR-25.4 / 30d")
 assert s.startswith("NO_MATCH_FOUND_IN_SEARCHED_SOURCE:")
 assert not may_conclude_nonexistence(s)

def test_broken_or_rate_limited_source_cannot_create_negative_evidence():
 for h in (SourceHealth.EMPTY_ANOMALY,SourceHealth.AUTH_REQUIRED,SourceHealth.RATE_LIMITED,SourceHealth.UNREACHABLE,SourceHealth.CHANGED_SCHEMA):
  assert negative_evidence_statement(source_by_id("KZ-UNIFIED-PROC"),p(h),EvidenceQuestion.CURRENT_PROCUREMENT,"x")=="UNKNOWN_SOURCE_HEALTH_OR_NONEMPTY"
  assert source_health_blocks_promotion(p(h))

def test_nonempty_search_is_not_negative_evidence():
 assert not empty_result_is_search_evidence(p(n=2))

def test_wrong_source_role_fails_before_empty_result():
 assert negative_evidence_statement(source_by_id("GLOBAL-COMTRADE"),p(),EvidenceQuestion.CURRENT_PROCUREMENT,"buyer x")=="SOURCE_NOT_FIT_FOR_QUESTION"
