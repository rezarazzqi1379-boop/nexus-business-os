"""Demand-trigger semantics: trigger evidence prioritizes investigation, never opportunity."""
from dataclasses import dataclass
TRIGGERS={"RFQ","TENDER","FAILED_PROCUREMENT","IMPORT_SHIPMENT","SHUTDOWN","OVERHAUL","EXPANSION","NEW_LINE","LOCALIZATION","SUPPLIER_CHANGE","STOCK_SHORTAGE"}

@dataclass(frozen=True)
class DemandTrigger:
 entity:str; kind:str; evidence_refs:tuple[str,...]; observed_at:str
 def validate(self):
  if self.kind not in TRIGGERS: raise ValueError("invalid_trigger")
  if not self.entity.strip() or not self.evidence_refs or not self.observed_at.strip(): raise ValueError("trigger_evidence_required")

def trigger_state(t:DemandTrigger)->str:
 t.validate(); return "INVESTIGATE"

def qualifies_opportunity(*args,**kwargs)->bool:
 return False
