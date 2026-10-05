"""Bridge validated trade measurements into UnifiedDataHub evidence."""
from __future__ import annotations
import hashlib
from unified_data_environment import EvidenceObservation,UnifiedDataHub
from steel_trade_records import TradeResult,validate_trade_result

def ingest_trade_result(hub:UnifiedDataHub,r:TradeResult,*,project_id:str="STEEL_SALES")->bool:
    errors=validate_trade_result(r)
    if errors: raise ValueError("invalid_trade_result:"+",".join(errors))
    q=r.query
    key="|".join((q.reporter,q.partner,q.hs,q.flow,q.period,r.source,r.source_ref))
    oid="trade-"+hashlib.sha256(key.encode()).hexdigest()[:20]
    metrics=[]
    if r.trade_value_usd is not None:metrics.append(f"value_usd={r.trade_value_usd}")
    if r.quantity is not None:metrics.append(f"quantity={r.quantity}")
    if r.net_weight_kg is not None:metrics.append(f"net_weight_kg={r.net_weight_kg}")
    statement=f"{q.flow} reporter={q.reporter} partner={q.partner} hs={q.hs} period={q.period}; "+", ".join(metrics)
    obs=EvidenceObservation(oid,project_id,"trade_measurement",statement,(r.source_ref,),r.observed_at,1.0)
    return hub.record_observation(obs)
