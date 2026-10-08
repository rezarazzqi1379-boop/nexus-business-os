from lead_evidence import LeadEvidenceRecord
from opportunity_recovery import *

def lead(**kw):
 d=dict(lead_id="L1",project_id="P1",entity_name="Buyer",entity_evidence=("e",),
        application_evidence=("a",),procurement_events=(),relationship_evidence=(),
        decision_maker_evidence=(),contact_evidence=(),compliance_state="UNKNOWN",
        freshness_state="UNKNOWN",contradictions=())
 d.update(kw);return LeadEvidenceRecord(**d)

def opt(oid,resolves,gain=1,p=.8,cost=1,project="P1"):
 return ResearchOption(oid,project,resolves,p,gain,cost,"PRIMARY","research "+oid)

def test_current_trigger_is_first_recoverable_blocker():
 assert blockers(lead())[0]==UnknownKind.CURRENT_TRIGGER

def test_information_gain_prefers_higher_expected_stage_gain_per_cost():
 r=lead()
 a=opt("broad-search",UnknownKind.CURRENT_TRIGGER,1,.5,2)
 b=opt("primary-portal",UnknownKind.CURRENT_TRIGGER,2,.8,1)
 assert next_research(r,(a,b)).option_id=="primary-portal"

def test_cross_project_option_is_never_selected():
 r=lead()
 assert next_research(r,(opt("wrong",UnknownKind.CURRENT_TRIGGER,project="P2"),)) is None

def test_contradiction_preempts_growth_research():
 r=lead(contradictions=("buyer identity conflict",))
 assert blockers(r)==(UnknownKind.CONTRADICTION,)
 assert next_research(r,(opt("more-leads",UnknownKind.CURRENT_TRIGGER),)) is None

def test_compliance_block_preempts_commercial_research():
 r=lead(compliance_state="BLOCKED")
 assert blockers(r)==(UnknownKind.COMPLIANCE,)
 assert next_research(r,(opt("buyer-search",UnknownKind.CURRENT_TRIGGER),)) is None

def test_invalid_probability_or_cost_has_zero_information_gain():
 assert information_gain(opt("bad",UnknownKind.CURRENT_TRIGGER,p=2))==0
 assert information_gain(opt("bad2",UnknownKind.CURRENT_TRIGGER,cost=0))==0

def test_recovery_snapshot_never_authorizes_action():
 r=lead()
 s=recovery_status(r,(opt("primary",UnknownKind.CURRENT_TRIGGER),))
 assert s["next_option"]=="primary"
 assert s["action_authorized"] is False

def test_no_research_when_evidence_ready():
 r=lead(procurement_events=("p",),relationship_evidence=("r",),decision_maker_evidence=("d",),
        contact_evidence=("c",),compliance_state="CLEAR",freshness_state="CURRENT")
 assert blockers(r)==()
 assert next_research(r,(opt("x",UnknownKind.CURRENT_TRIGGER),)) is None
