from conversion_first_router import *
def test_named_geometry_shipment_can_research_without_stock_but_not_convert():
 assert demand_route(named_buyer=True,geometry_visible=True,shipment_specific=True,current_stock_record=None)=="RESEARCH_ONLY_AWAIT_STOCK"
def test_weak_demand_is_rejected_before_stock():
 assert demand_route(named_buyer=True,geometry_visible=False,shipment_specific=True)=="REJECT_INSUFFICIENT_DEMAND_EVIDENCE"
def test_conversion_gate_never_weakens_for_missing_stock_or_relationship():
 assert evidence_ready(buyer=True,demand_current=True,geometry=True,technical_fit=True,current_stock=False,relationship=True) is False
 assert evidence_ready(buyer=True,demand_current=True,geometry=True,technical_fit=True,current_stock=True,relationship=False) is False
