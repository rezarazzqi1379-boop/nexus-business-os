"""Shipment-specific relationship binding: aggregate supplier evidence cannot bind a shipment."""
from dataclasses import dataclass
@dataclass(frozen=True)
class ShipmentBinding:
 shipment_ref:str
 buyer_ref:str
 supplier_ref:str|None=None
 aggregate_supplier_refs:tuple[str,...]=()
def supplier_state(s:ShipmentBinding)->str:
 if not s.shipment_ref or not s.buyer_ref: raise ValueError("shipment_and_buyer_required")
 return "SHIPMENT_SUPPLIER_BOUND" if s.supplier_ref else "SUPPLIER_UNKNOWN"
def aggregate_can_bind_supplier(s:ShipmentBinding)->bool:
 return False
