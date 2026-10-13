"""Conversion-first routing: research may continue while sellable-stock promotion stays fail-closed."""
from stock_evidence_contract import stock_evidence_state
def sellable_stock_state(record:dict)->str:
 return "SELLABLE_CONFIRMED" if stock_evidence_state(record)=="CURRENT_STOCK_EVIDENCED" else "STOCK_UNCONFIRMED"
def demand_route(*, named_buyer:bool, geometry_visible:bool, shipment_specific:bool, current_stock_record:dict|None=None)->str:
 if not (named_buyer and geometry_visible and shipment_specific): return "REJECT_INSUFFICIENT_DEMAND_EVIDENCE"
 if not current_stock_record or sellable_stock_state(current_stock_record)!="SELLABLE_CONFIRMED": return "RESEARCH_ONLY_AWAIT_STOCK"
 return "CONVERSION_REVIEW"
def evidence_ready(*,buyer:bool,demand_current:bool,geometry:bool,technical_fit:bool,current_stock:bool,relationship:bool)->bool:
 return all((buyer,demand_current,geometry,technical_fit,current_stock,relationship))
