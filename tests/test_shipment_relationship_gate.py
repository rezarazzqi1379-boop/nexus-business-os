from shipment_relationship_gate import *
def test_aggregate_supplier_table_cannot_bind_specific_shipment():
 s=ShipmentBinding("shipment:2026-01-29","buyer:ecuador",None,("top_supplier:A","top_supplier:B"))
 assert supplier_state(s)=="SUPPLIER_UNKNOWN"
 assert aggregate_can_bind_supplier(s) is False
