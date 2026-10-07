"""Tender evidence routing: exact geometry never substitutes for material specification."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TenderEvidence:
 buyer:str; open_now:bool; grade_or_spec:str=""; geometry:str=""; technical_condition:str=""; ndt:str=""
def route_tender(x:TenderEvidence)->str:
 if not x.buyer.strip(): return "REJECT_UNNAMED_BUYER"
 if not x.open_now: return "HISTORICAL_DEMAND_DNA"
 if not x.grade_or_spec.strip(): return "RESOLVE_MATERIAL_SPEC"
 if not x.geometry.strip(): return "RESOLVE_GEOMETRY"
 if not x.technical_condition.strip() or not x.ndt.strip(): return "TECHNICAL_ACCEPTANCE_INCOMPLETE"
 return "TECHNICAL_REVIEW_READY"
