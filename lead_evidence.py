"""Evidence-native customer discovery record and qualification gate."""
from dataclasses import dataclass
from enum import Enum

class LeadState(str,Enum):
 DISCOVERED="DISCOVERED"; EVIDENCED="EVIDENCED"; DEMAND_SIGNAL="DEMAND_SIGNAL"; BUYER_VERIFIED="BUYER_VERIFIED"; CONTACTABLE="CONTACTABLE"; EVIDENCE_READY="EVIDENCE_READY"; BLOCKED="BLOCKED"

@dataclass(frozen=True)
class LeadEvidenceRecord:
 lead_id:str
 project_id:str
 entity_name:str
 entity_evidence:tuple[str,...]
 application_evidence:tuple[str,...]=()
 procurement_events:tuple[str,...]=()
 relationship_evidence:tuple[str,...]=()
 decision_maker_evidence:tuple[str,...]=()
 contact_evidence:tuple[str,...]=()
 compliance_state:str="UNKNOWN"
 freshness_state:str="UNKNOWN"
 contradictions:tuple[str,...]=()
 negative_evidence:tuple[str,...]=()

def qualify_lead(r:LeadEvidenceRecord)->LeadState:
 if not r.lead_id or not r.project_id or not r.entity_name or not r.entity_evidence:
  return LeadState.DISCOVERED
 if r.contradictions or r.compliance_state=="BLOCKED":
  return LeadState.BLOCKED
 if not r.application_evidence:
  return LeadState.EVIDENCED
 if not r.procurement_events or r.freshness_state!="CURRENT":
  return LeadState.EVIDENCED
 if not r.relationship_evidence:
  return LeadState.DEMAND_SIGNAL
 if not r.decision_maker_evidence:
  return LeadState.BUYER_VERIFIED
 if not r.contact_evidence:
  return LeadState.BUYER_VERIFIED
 if r.compliance_state!="CLEAR":
  return LeadState.CONTACTABLE
 return LeadState.EVIDENCE_READY

def lead_evidence_score(r:LeadEvidenceRecord)->int:
 parts=(r.entity_evidence,r.application_evidence,r.procurement_events,r.relationship_evidence,r.decision_maker_evidence,r.contact_evidence)
 score=sum(bool(x) for x in parts)*15
 score+=10 if r.freshness_state=="CURRENT" else 0
 score+=10 if r.compliance_state=="CLEAR" else 0
 score-=25 if r.contradictions else 0
 return max(0,min(100,score))
