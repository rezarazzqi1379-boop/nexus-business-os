"""Evidence-bound customer intelligence and sales-motion selection."""
from dataclasses import dataclass
from enum import Enum

class SalesMotion(str,Enum):
 RESEARCH="RESEARCH"; PROCUREMENT_LED="PROCUREMENT_LED"; RELATIONSHIP_LED="RELATIONSHIP_LED"; TECHNICAL_QUALIFICATION="TECHNICAL_QUALIFICATION"; HOLD="HOLD"

@dataclass(frozen=True)
class CustomerProfile:
 project_id:str; company_id:str; industry:str; process:str; product_need:str
 current_demand_evidence:bool=False; procurement_portal:bool=False
 supplier_registration:bool=False; relationship_path:bool=False
 technical_gatekeeper:bool=False; verified_contact:bool=False
 compliance_clear:bool=False; contradictions:bool=False
 independent_origins:int=0

def choose_sales_motion(p:CustomerProfile)->SalesMotion:
 if p.contradictions or not p.project_id or not p.company_id: return SalesMotion.HOLD
 if not p.current_demand_evidence or p.independent_origins<2: return SalesMotion.RESEARCH
 if p.procurement_portal or p.supplier_registration: return SalesMotion.PROCUREMENT_LED
 if p.technical_gatekeeper and not p.relationship_path: return SalesMotion.TECHNICAL_QUALIFICATION
 if p.relationship_path: return SalesMotion.RELATIONSHIP_LED
 return SalesMotion.RESEARCH

def evidence_ready_for_outreach(p:CustomerProfile)->bool:
 """Readiness only; external outreach still requires the NEXUS action gate."""
 return bool(
  choose_sales_motion(p) in {SalesMotion.PROCUREMENT_LED,SalesMotion.RELATIONSHIP_LED}
  and p.verified_contact and p.compliance_clear and not p.contradictions
 )
