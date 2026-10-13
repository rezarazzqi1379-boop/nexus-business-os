"""Explainable country Market Digital Twin baseline; missing evidence never becomes a zero-risk score."""
from dataclasses import dataclass
@dataclass(frozen=True)
class MarketTwin:
 country:str; demand:float|None=None; trade_flow:float|None=None; buyer_density:float|None=None
 logistics:float|None=None; payment:float|None=None; compliance:float|None=None; evidence_refs:tuple[str,...]=()
def rank_score(x:MarketTwin):
 vals=(x.demand,x.trade_flow,x.buyer_density,x.logistics,x.payment,x.compliance)
 if not x.country.strip() or not x.evidence_refs:return None
 if any(v is not None and not 0<=v<=1 for v in vals):raise ValueError("market_factor_must_be_0_1")
 known=[v for v in vals if v is not None]
 if len(known)<4:return None
 return round(sum(known)/len(known),4)
