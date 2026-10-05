"""Deterministic country opportunity queue; ranking inputs stay independent and auditable."""
from dataclasses import dataclass
@dataclass(frozen=True)
class OpportunityCandidate:
 opportunity_id:str; country:str; company:str; buyer_fit:int; strategic_value:int; evidence_quality:int
 compliance_ready:bool=False
def queue_score(x:OpportunityCandidate)->int:
 vals=(x.buyer_fit,x.strategic_value,x.evidence_quality)
 if any(v<0 or v>100 for v in vals):raise ValueError("scores_must_be_0_100")
 return round(.45*x.buyer_fit+.35*x.strategic_value+.20*x.evidence_quality)
def build_country_queue(items):
 return tuple(sorted(items,key=lambda x:(-queue_score(x),x.opportunity_id)))
