"""Opportunity recovery and information-gain selector.

Chooses the smallest next research action for a stalled commercial lead.
Ranking never overrides contradiction, compliance, project isolation, or action gates.
"""
from dataclasses import dataclass
from enum import Enum
from lead_evidence import LeadEvidenceRecord,LeadState,qualify_lead

class UnknownKind(str,Enum):
 ENTITY="ENTITY"; APPLICATION="APPLICATION"; CURRENT_TRIGGER="CURRENT_TRIGGER"
 RELATIONSHIP="RELATIONSHIP"; DECISION_MAKER="DECISION_MAKER"; CONTACT="CONTACT"
 COMPLIANCE="COMPLIANCE"; CONTRADICTION="CONTRADICTION"

@dataclass(frozen=True)
class ResearchOption:
 option_id:str; project_id:str; resolves:UnknownKind
 expected_resolution:float; stage_gain:int; cost:float
 source_role:str; action:str

def blockers(r:LeadEvidenceRecord)->tuple[UnknownKind,...]:
 if r.contradictions:return (UnknownKind.CONTRADICTION,)
 if r.compliance_state=="BLOCKED":return (UnknownKind.COMPLIANCE,)
 out=[]
 if not r.entity_evidence:out.append(UnknownKind.ENTITY)
 if not r.application_evidence:out.append(UnknownKind.APPLICATION)
 if not r.procurement_events or r.freshness_state!="CURRENT":out.append(UnknownKind.CURRENT_TRIGGER)
 if not r.relationship_evidence:out.append(UnknownKind.RELATIONSHIP)
 if not r.decision_maker_evidence:out.append(UnknownKind.DECISION_MAKER)
 if not r.contact_evidence:out.append(UnknownKind.CONTACT)
 if r.compliance_state!="CLEAR":out.append(UnknownKind.COMPLIANCE)
 return tuple(out)

def information_gain(o:ResearchOption)->float:
 if not 0<=o.expected_resolution<=1 or o.stage_gain<0 or o.cost<=0:return 0.0
 return round((o.expected_resolution*o.stage_gain)/o.cost,4)

def next_research(r:LeadEvidenceRecord,options:tuple[ResearchOption,...])->ResearchOption|None:
 bs=blockers(r)
 if not bs:return None
 if bs[0] in {UnknownKind.CONTRADICTION,UnknownKind.COMPLIANCE}:
  target=bs[0]
 else:
  target=bs[0]
 eligible=[o for o in options if o.project_id==r.project_id and o.resolves==target and o.action.strip()]
 if not eligible:return None
 return max(eligible,key=lambda o:(information_gain(o),o.expected_resolution,-o.cost,o.option_id))

def recovery_status(r:LeadEvidenceRecord,options:tuple[ResearchOption,...])->dict:
 state=qualify_lead(r)
 nxt=next_research(r,options)
 return {
  "lead_id":r.lead_id,
  "state":state.value,
  "blockers":tuple(x.value for x in blockers(r)),
  "next_option":nxt.option_id if nxt else "",
  "next_action":nxt.action if nxt else "",
  "expected_information_gain":information_gain(nxt) if nxt else 0.0,
  "action_authorized":False,
 }
