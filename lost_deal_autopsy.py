"""Lost-deal autopsy and evidence-aware experience distillation."""
from dataclasses import dataclass
REASONS={"PRICE","DELIVERY","SPECIFICATION","QUALITY","TRUST","PAYMENT","LOGISTICS","COMPETITOR","TIMING","NO_RESPONSE","COMPLIANCE","INTERNAL_FAILURE","UNKNOWN"}
@dataclass(frozen=True)
class LostDeal:
 opportunity_id:str; reason:str; evidence_refs:tuple[str,...]; country:str=""; application:str=""; product:str=""
def validate_lost_deal(x:LostDeal)->tuple[str,...]:
 e=[]
 if not x.opportunity_id.strip():e.append("opportunity_id_required")
 if x.reason not in REASONS:e.append("invalid_reason")
 if x.reason!="UNKNOWN" and not x.evidence_refs:e.append("specific_loss_reason_requires_evidence")
 return tuple(e)
def distill_failure_pattern(items,minimum_cases=3):
 valid=[x for x in items if not validate_lost_deal(x) and x.reason!="UNKNOWN"]
 counts={}
 refs={}
 for x in valid:
  key=(x.reason,x.country,x.application,x.product)
  counts[key]=counts.get(key,0)+1;refs.setdefault(key,set()).update(x.evidence_refs)
 out=[]
 for key,n in counts.items():
  status="LESSON" if n>=minimum_cases else "HYPOTHESIS"
  out.append({"status":status,"pattern":key,"cases":n,"evidence_refs":tuple(sorted(refs[key]))})
 return tuple(sorted(out,key=lambda x:(-x["cases"],x["pattern"])))
