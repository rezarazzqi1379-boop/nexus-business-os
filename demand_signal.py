"""Governed Demand Signal records for NEXUS v3."""
from dataclasses import dataclass
SIGNALS={"NEW_PLANT","PLANT_EXPANSION","CAPEX","TENDER","NEW_CONTRACT","PRODUCTION_INCREASE","MAINTENANCE_SHUTDOWN","EQUIPMENT_UPGRADE","NEW_PRODUCT_LINE","HIRING_SURGE","PROCUREMENT_NOTICE","IMPORT_SPIKE","SUPPLIER_CHANGE","SUPPLIER_FAILURE","LOGISTICS_DISRUPTION","PRICE_CHANGE","INVENTORY_SHORTAGE","COMPETITOR_EXIT","CERTIFICATION","NEW_PROJECT","GOVERNMENT_INVESTMENT"}
@dataclass(frozen=True)
class DemandSignal:
    company:str; country:str; signal_type:str; observed_at:str; evidence_refs:tuple[str,...]
    potential_need:str=""; plant:str=""
def validate_signal(s:DemandSignal)->tuple[str,...]:
    errors=[]
    if s.signal_type not in SIGNALS: errors.append("invalid_signal_type")
    if not s.company.strip() or not s.country.strip(): errors.append("company_country_required")
    if not s.evidence_refs: errors.append("signal_evidence_required")
    if not s.observed_at.strip(): errors.append("observed_at_required")
    return tuple(errors)
def signal_to_opportunity_state(s:DemandSignal)->str:
    return "HYPOTHESIS" if not validate_signal(s) else "UNKNOWN"
