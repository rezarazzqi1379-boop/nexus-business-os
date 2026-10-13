"""Commercial outcome measurement for NEXUS v7.

Measures funnel outcomes without inventing attribution. Improvement requires
comparable baseline/candidate observations and outcome evidence.
"""
from dataclasses import dataclass

@dataclass(frozen=True)
class Funnel:
 discovered:int; qualified:int; contacted:int; rfqs:int; quotes:int; negotiations:int; orders:int
 commercial_value:float=0.0; outcome_evidence_refs:tuple[str,...]=()
 def validate(self):
  xs=(self.discovered,self.qualified,self.contacted,self.rfqs,self.quotes,self.negotiations,self.orders)
  if any(type(x) is not int or x<0 for x in xs) or self.commercial_value<0:raise ValueError("invalid_funnel")
  if not all(a>=b for a,b in zip(xs,xs[1:])):raise ValueError("non_monotonic_funnel")

def rates(x:Funnel)->dict:
 x.validate()
 def r(n,d):return None if d==0 else n/d
 return {"qualification":r(x.qualified,x.discovered),"rfq":r(x.rfqs,x.contacted),
 "quote":r(x.quotes,x.rfqs),"negotiation":r(x.negotiations,x.quotes),
 "order":r(x.orders,x.negotiations)}

def compare(base:Funnel,cand:Funnel)->dict:
 base.validate();cand.validate()
 if not base.outcome_evidence_refs or not cand.outcome_evidence_refs:
  return {"state":"INSUFFICIENT_OUTCOME_EVIDENCE","improved":False}
 br,cr=rates(base),rates(cand)
 comparable={k:(br[k],cr[k]) for k in br if br[k] is not None and cr[k] is not None}
 deltas={k:c-b for k,(b,c) in comparable.items()}
 value_delta=cand.commercial_value-base.commercial_value
 # Do not call improvement from activity volume. Require at least one conversion
 # improvement or positive evidenced commercial value, and no order-rate regression.
 order_regressed="order" in deltas and deltas["order"]<0
 improved=(any(v>0 for v in deltas.values()) or value_delta>0) and not order_regressed
 return {"state":"MEASURED","improved":improved,"rate_deltas":deltas,"commercial_value_delta":value_delta}
