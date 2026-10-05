"""Thin procurement graph integrated with NEXUS evidence semantics."""
from dataclasses import dataclass
from commercial_chain_graph import ChainEdge

STATES={"OPEN_DEMAND","AWARDED","CLOSED_UNKNOWN","CANCELLED","HISTORICAL"}
AWARD_STATES={"UNKNOWN","AWARDED","NOT_AWARDED"}

@dataclass(frozen=True)
class ProcurementNode:
 procurement_id:str; buyer:str; legal_entity:str; product:str
 grade:str=""; standard:str=""; form:str=""; dimensions:tuple[str,...]=()
 quantity:float|None=None; quantity_unit:str=""; delivery_requirements:str=""
 publication_date:str=""; deadline:str=""; status:str="OPEN_DEMAND"; platform:str=""
 procurement_contact:str=""; award_status:str="UNKNOWN"; winner_supplier:str=""
 contract_ref:str=""; evidence_refs:tuple[str,...]=(); source_families:tuple[str,...]=(); observed_at:str=""
 def validate(self)->tuple[str,...]:
  e=[]
  if not all(x.strip() for x in (self.procurement_id,self.buyer,self.product)):e.append("identity_required")
  if self.status not in STATES:e.append("invalid_status")
  if self.award_status not in AWARD_STATES:e.append("invalid_award_status")
  if not self.evidence_refs:e.append("evidence_required")
  if self.quantity is not None and self.quantity<=0:e.append("invalid_quantity")
  if self.award_status=="AWARDED" and not self.winner_supplier.strip():e.append("winner_required_for_award")
  if self.winner_supplier.strip() and self.award_status!="AWARDED":e.append("winner_without_award")
  return tuple(e)

def published_demand_edge(p:ProcurementNode)->ChainEdge:
 if p.validate():raise ValueError("invalid_procurement")
 return ChainEdge(p.buyer,"PUBLISHED_DEMAND",p.procurement_id,"CANDIDATE",p.evidence_refs,p.observed_at,p.source_families)

def award_edge(p:ProcurementNode)->ChainEdge|None:
 if p.validate() or p.award_status!="AWARDED":return None
 return ChainEdge(p.buyer,"AWARDED_TO",p.winner_supplier,"CANDIDATE",p.evidence_refs,p.observed_at,p.source_families)
