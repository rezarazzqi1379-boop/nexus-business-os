"""Evidence gate for stock-to-demand commercial conversion."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ConversionEvidence:
 buyer_identity_refs:tuple[str,...]
 demand_refs:tuple[str,...]
 geometry_refs:tuple[str,...]
 technical_refs:tuple[str,...]
 stock_current_refs:tuple[str,...]
 eico_relationship_refs:tuple[str,...]
def state(e:ConversionEvidence)->str:
 missing=[]
 for name in ("buyer_identity_refs","demand_refs","geometry_refs","technical_refs","stock_current_refs","eico_relationship_refs"):
  if not getattr(e,name): missing.append(name)
 return "EVIDENCE_READY" if not missing else "PARTIAL_MISSING:"+",".join(missing)
def shipment_to_buyer_is_eico_relationship(*args,**kwargs)->bool:
 return False
