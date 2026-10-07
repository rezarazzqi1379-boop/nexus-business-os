"""Reverse-buyer discovery contracts: trade/competitor/project signals produce candidates, never verified buyers."""
from dataclasses import dataclass
ROUTES={"TRADE","COMPETITOR","PROJECT"}
@dataclass(frozen=True)
class ReverseDiscovery:
    route:str; country:str; application:str; company:str
    evidence_refs:tuple[str,...]; observed_at:str
    hs_candidate:str=""; source_entity:str=""; plant:str=""
def validate_reverse_discovery(x:ReverseDiscovery)->tuple[str,...]:
    e=[]
    if x.route not in ROUTES:e.append("invalid_route")
    if not x.country.strip() or not x.application.strip() or not x.company.strip():e.append("country_application_company_required")
    if not x.evidence_refs:e.append("evidence_required")
    if not x.observed_at.strip():e.append("observed_at_required")
    if x.route=="TRADE" and (not x.hs_candidate.isdigit() or len(x.hs_candidate)<4):e.append("trade_route_hs_candidate_required")
    return tuple(e)
def candidate_state(x:ReverseDiscovery)->str:
    return "HYPOTHESIS" if not validate_reverse_discovery(x) else "UNKNOWN"
