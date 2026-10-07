from customer_sales_motion import *

def p(**kw):
 d=dict(project_id="CHAIN-SALES",company_id="C",industry="cement",process="conveyor",product_need="roller chain"); d.update(kw); return CustomerProfile(**d)
def test_directory_name_alone_is_not_sales_ready():
 assert choose_sales_motion(p())==SalesMotion.RESEARCH
def test_single_source_demand_is_not_enough():
 assert choose_sales_motion(p(current_demand_evidence=True,independent_origins=1,procurement_portal=True))==SalesMotion.RESEARCH
def test_portal_buyer_uses_procurement_motion():
 assert choose_sales_motion(p(current_demand_evidence=True,independent_origins=2,procurement_portal=True))==SalesMotion.PROCUREMENT_LED
def test_technical_gatekeeper_precedes_cold_outreach_when_no_relationship():
 assert choose_sales_motion(p(current_demand_evidence=True,independent_origins=2,technical_gatekeeper=True))==SalesMotion.TECHNICAL_QUALIFICATION
def test_relationship_motion_requires_evidence():
 assert choose_sales_motion(p(current_demand_evidence=True,independent_origins=2,relationship_path=True))==SalesMotion.RELATIONSHIP_LED
def test_outreach_readiness_does_not_bypass_contact_or_compliance():
 q=p(current_demand_evidence=True,independent_origins=2,relationship_path=True,verified_contact=True,compliance_clear=False)
 assert not evidence_ready_for_outreach(q)
def test_contradiction_fail_closed():
 assert choose_sales_motion(p(current_demand_evidence=True,independent_origins=3,procurement_portal=True,contradictions=True))==SalesMotion.HOLD
