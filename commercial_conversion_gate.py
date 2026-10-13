"""Commercial conversion gate joins relationship, demand and technical evidence."""
from dataclasses import dataclass

@dataclass(frozen=True)
class ConversionEvidence:
 entity:str
 relationship_refs:tuple[str,...]=()
 demand_refs:tuple[str,...]=()
 technical_refs:tuple[str,...]=()
 current_refs:tuple[str,...]=()

def conversion_state(e:ConversionEvidence)->str:
 if not e.entity.strip(): raise ValueError("entity_required")
 if e.relationship_refs and e.demand_refs and e.technical_refs and e.current_refs:
  return "EVIDENCE_READY"
 if e.relationship_refs and e.technical_refs:
  return "RELATIONSHIP_TECHNICAL_ONLY"
 if e.demand_refs and e.technical_refs:
  return "DEMAND_TECHNICAL_ONLY"
 return "INSUFFICIENT_BINDING"

def verified_commercial_conversion(e:ConversionEvidence)->bool:
 return conversion_state(e)=="EVIDENCE_READY"
