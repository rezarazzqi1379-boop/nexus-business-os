"""Lost-deal autopsy: repeated observations become patterns, not lessons without validation."""
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
 groups={}
 for x in valid:
  key=(x.reason,x.country,x.application,x.product)
  groups.setdefault(key,{})[x.opportunity_id]=x
 out=[]
 for key,by_opp in groups.items():
  xs=tuple(by_opp.values()); refs={r for x in xs for r in x.evidence_refs}
  context_complete=all(key[1:])
  distinct_evidence=len(refs)>=len(xs)
  status="FAILURE_PATTERN" if len(xs)>=minimum_cases and context_complete and distinct_evidence else "HYPOTHESIS"
  out.append({"status":status,"pattern":key,"cases":len(xs),"evidence_refs":tuple(sorted(refs))})
 return tuple(sorted(out,key=lambda x:(-x["cases"],x["pattern"])))
def promote_pattern(pattern,*,eval_evidence_refs:tuple[str,...],replicated:bool)->str:
 if pattern.get("status")!="FAILURE_PATTERN":return "NOT_READY"
 if not replicated or not eval_evidence_refs:return "FAILURE_PATTERN"
 return "LESSON"
