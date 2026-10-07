"""Research-only demand evidence gate for stock-blocked commercial discovery."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DemandEvidence:
 buyer:str; evidence_type:str; source_locator:str; observed_at:str; geometry:str; product:str; current_open:bool=False
def research_state(x:DemandEvidence)->str:
 if not all(v.strip() for v in (x.buyer,x.evidence_type,x.source_locator,x.observed_at,x.geometry,x.product)):
  return "REJECT_INCOMPLETE_EVIDENCE"
 if x.evidence_type not in {"RFQ","BUY_TENDER","PURCHASE_PLAN","SHIPMENT","AWARD","PURCHASE_SPEC"}:
  return "REJECT_NON_BUYER_SIDE_EVIDENCE"
 return "CURRENT_DEMAND_SIGNAL" if x.current_open else "HISTORICAL_OR_OBSERVED_SIGNAL"
def conversion_state(x:DemandEvidence, *, current_stock:bool, technical_fit:bool, relationship:bool)->str:
 if research_state(x).startswith("REJECT"): return "REJECT"
 if not x.current_open: return "RESEARCH_ONLY_CURRENTNESS_UNPROVEN"
 if not current_stock: return "RESEARCH_ONLY_AWAIT_STOCK"
 if not technical_fit: return "ENGINEERING_REVIEW"
 if not relationship: return "RELATIONSHIP_UNKNOWN"
 return "EVIDENCE_READY"
