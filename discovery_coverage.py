"""Market-layer coverage guard for NEXUS commercial discovery."""
from __future__ import annotations

REQUIRED_MARKET_LAYERS=(
 "MANUFACTURER","TRADER","STOCKIST","IMPORTER","DISTRIBUTOR",
 "SERVICE_CENTER","END_USER","OEM","COMPETITOR","PROJECT_EPC",
 "DECISION_MAKER","TRADE_FLOW","PRICE","LOGISTICS","PAYMENT",
 "COMPLIANCE","DEMAND_SIGNALS",
)
COVERAGE_STATES={
 "COVERED","PARTIAL","NOT_SEARCHED","NO_EVIDENCE","NEGATIVE_EVIDENCE",
 "CONTRADICTORY_EVIDENCE","STALE_EVIDENCE","SOURCE_UNAVAILABLE",
}
CHECKED_STATES={
 "COVERED","PARTIAL","NO_EVIDENCE","NEGATIVE_EVIDENCE",
 "CONTRADICTORY_EVIDENCE","STALE_EVIDENCE",
}

def evaluate_market_coverage(states:dict[str,str],required=REQUIRED_MARKET_LAYERS)->dict:
    invalid={k:v for k,v in states.items() if v not in COVERAGE_STATES}
    missing=tuple(x for x in required if x not in states)
    blind=tuple(x for x in required if states.get(x) in {None,"NOT_SEARCHED","SOURCE_UNAVAILABLE"})
    checked=tuple(x for x in required if states.get(x) in CHECKED_STATES)
    complete=not invalid and not missing and not blind
    return {"complete":complete,"checked":checked,"blind":blind,"missing":missing,"invalid":invalid}

def can_mark_market_discovery_complete(states:dict[str,str],required=REQUIRED_MARKET_LAYERS)->bool:
    return bool(evaluate_market_coverage(states,required)["complete"])

from dataclasses import dataclass

@dataclass(frozen=True)
class CoverageCell:
    country:str
    industry:str
    product:str
    application:str
    buyer_type:str
    source_type:str
    discovery_method:str
    state:str="NOT_CHECKED"

def evidence_state(cell:CoverageCell)->str:
    return cell.state if cell.state in COVERAGE_STATES else "NOT_CHECKED"

def blind_cells(cells):
    return tuple(c for c in cells if evidence_state(c) in {"NOT_CHECKED","NOT_SEARCHED","SOURCE_UNAVAILABLE"})
