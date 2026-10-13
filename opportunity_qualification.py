"""Evidence-safe procurement opportunity qualification."""
from dataclasses import dataclass

DECISIONS={"PURSUE","INVESTIGATE","WATCH","REJECT"}
FIT_ORDER={"NO_FIT":0,"UNKNOWN":1,"ENGINEERING_REVIEW":2,"POTENTIAL_FIT":3,"EXACT_FIT":4}
CRITICAL=("product_fit","evidence_quality","recency","logistics","payment","compliance","deadline_feasibility")

@dataclass(frozen=True)
class OpportunityAssessment:
 opportunity_id:str; product_fit:str
 evidence_quality:float|None=None; recency:float|None=None; buyer_value:float|None=None
 relationship_access:float|None=None; competition:float|None=None; logistics:float|None=None
 payment:float|None=None; compliance:float|None=None; deadline_feasibility:float|None=None
 def validate(self):
  if self.product_fit not in FIT_ORDER:raise ValueError("invalid_fit")
  for k,v in self.__dict__.items():
   if k not in {"opportunity_id","product_fit"} and v is not None and not 0<=v<=1:raise ValueError("invalid_score")

def qualify(x:OpportunityAssessment)->tuple[str,tuple[str,...]]:
 x.validate();missing=tuple(k for k in CRITICAL if (k=="product_fit" and x.product_fit=="UNKNOWN") or (k!="product_fit" and getattr(x,k) is None))
 if x.product_fit=="NO_FIT":return "REJECT",("no_product_fit",)
 if missing:return "INVESTIGATE",tuple("unknown:"+k for k in missing)
 if x.product_fit=="ENGINEERING_REVIEW":return "INVESTIGATE",("engineering_review",)
 vals=[x.evidence_quality,x.recency,x.logistics,x.payment,x.compliance,x.deadline_feasibility]
 if any(v is not None and v<.4 for v in vals):return "WATCH",("critical_dimension_weak",)
 if x.product_fit in {"EXACT_FIT","POTENTIAL_FIT"} and all(v is not None and v>=.6 for v in vals):return "PURSUE",()
 return "INVESTIGATE",("insufficient_confidence",)
