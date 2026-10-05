"""Deterministic country opportunity queue; ranking inputs stay independent and auditable."""
from dataclasses import dataclass
from decimal import Decimal,ROUND_HALF_UP
@dataclass(frozen=True)
class OpportunityCandidate:
 opportunity_id:str; country:str; company:str; buyer_fit:int; strategic_value:int; evidence_quality:int
 compliance_ready:bool=False
def queue_score(x:OpportunityCandidate)->int:
 vals=(x.buyer_fit,x.strategic_value,x.evidence_quality)
 if any(v<0 or v>100 for v in vals):raise ValueError("scores_must_be_0_100")
 raw=Decimal(x.buyer_fit)*Decimal("0.45")+Decimal(x.strategic_value)*Decimal("0.35")+Decimal(x.evidence_quality)*Decimal("0.20")
 return int(raw.quantize(Decimal("1"),rounding=ROUND_HALF_UP))
def build_country_queue(items):
 return tuple(sorted(items,key=lambda x:(-queue_score(x),x.opportunity_id)))
