from steel_mtc_intake import *
def R(**kw):
 d=dict(project_id="STEEL",certificate_number="C1",issuing_date="2026-01-01",standard="EN 10204 3.1",heat_number="H1",source_ref="DOC1",extraction_confidence=.9,chemical_rows=1,mechanical_rows=1);d.update(kw);return MTCRecord(**d)
def test_required_traceability_fields():
 ok,m=validate_mtc(R(heat_number="")); assert not ok and "heat_number" in m
def test_low_confidence_escalates():
 assert review_route(R(extraction_confidence=.4))=="MANUAL_OR_VISION_REVIEW"
def test_missing_tables_needs_completeness_review():
 assert review_route(R(mechanical_rows=0))=="COMPLETENESS_REVIEW"
def test_extraction_never_equals_standard_compliance():
 assert not may_claim_standard_compliance(R())
def test_good_structured_record_is_review_ready_not_approved():
 assert review_route(R())=="STRUCTURED_REVIEW_READY"
