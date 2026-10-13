from red_team_max import *
from sales_readiness import overall_readiness

def test_category_recurrence_cannot_promote_grade_recurrence():
 assert recurring_grade(same_grade_events=1,category_events=7) is False

def test_historical_supplier_not_current_without_current_evidence():
 assert historical_edge_may_be_current(historical=True,current_evidence_refs=()) is False

def test_contact_role_not_authority_without_authority_evidence():
 assert contact_is_authority(role_evidence=("tender-contact",),authority_evidence=()) is False

def test_unknown_compliance_blocks_ready():
 assert opportunity_requires_compliance({"TECHNICAL":"READY","COMMERCIAL":"READY","COMPLIANCE":"UNKNOWN","CONTACT":"READY"}) is False
