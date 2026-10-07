from lead_evidence import *

def base(**kw):
 d=dict(lead_id="L1",project_id="PRJ-X",entity_name="Buyer",entity_evidence=("src:entity",))
 d.update(kw); return LeadEvidenceRecord(**d)

def test_company_name_is_not_customer():
 assert qualify_lead(base())==LeadState.EVIDENCED

def test_historical_or_stale_signal_is_not_current_demand():
 r=base(application_evidence=("src:app",),procurement_events=("historical shipment",),freshness_state="STALE")
 assert qualify_lead(r)==LeadState.EVIDENCED

def test_current_procurement_without_relationship_is_only_demand_signal():
 r=base(application_evidence=("src:app",),procurement_events=("current rfq",),freshness_state="CURRENT")
 assert qualify_lead(r)==LeadState.DEMAND_SIGNAL

def test_contact_does_not_bypass_unknown_compliance():
 r=base(application_evidence=("a",),procurement_events=("p",),relationship_evidence=("r",),decision_maker_evidence=("d",),contact_evidence=("c",),freshness_state="CURRENT")
 assert qualify_lead(r)==LeadState.CONTACTABLE

def test_clear_evidence_stack_reaches_evidence_ready():
 r=base(application_evidence=("a",),procurement_events=("p",),relationship_evidence=("r",),decision_maker_evidence=("d",),contact_evidence=("c",),freshness_state="CURRENT",compliance_state="CLEAR")
 assert qualify_lead(r)==LeadState.EVIDENCE_READY

def test_contradiction_or_blocked_compliance_fails_closed():
 assert qualify_lead(base(contradictions=("identity mismatch",)))==LeadState.BLOCKED
 assert qualify_lead(base(compliance_state="BLOCKED"))==LeadState.BLOCKED

def test_negative_evidence_is_preserved_not_promoted():
 r=base(application_evidence=("a",),negative_evidence=("no current procurement found",))
 assert r.negative_evidence and qualify_lead(r)==LeadState.EVIDENCED
