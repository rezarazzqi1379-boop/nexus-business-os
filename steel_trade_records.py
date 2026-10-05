"""Normalized trade query/result records for evidence-native providers."""
from __future__ import annotations
from dataclasses import dataclass
@dataclass(frozen=True)
class TradeQuery:
    reporter:str; partner:str; hs:str; flow:str; period:str
@dataclass(frozen=True)
class TradeResult:
    query:TradeQuery; source:str; observed_at:str
    trade_value_usd:float|None=None; quantity:float|None=None; net_weight_kg:float|None=None
    source_ref:str=""
def validate_trade_result(r:TradeResult)->tuple[str,...]:
    e=[]
    if r.query.flow not in {"IMPORT","EXPORT"}:e.append("invalid_flow")
    if not (2<=len(r.query.hs)<=10 and r.query.hs.isdigit()):e.append("invalid_hs")
    if not r.source.strip():e.append("source_required")
    if not r.source_ref.strip():e.append("source_ref_required")
    if not r.observed_at.strip():e.append("observed_at_required")
    if r.trade_value_usd is None and r.quantity is None and r.net_weight_kg is None:e.append("no_measurement")
    for name,v in (("trade_value_usd",r.trade_value_usd),("quantity",r.quantity),("net_weight_kg",r.net_weight_kg)):
        if v is not None and v<0:e.append(f"negative:{name}")
    return tuple(e)
