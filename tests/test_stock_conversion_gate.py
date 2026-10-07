from stock_conversion_gate import *
def test_geometry_compatible_named_buyer_not_ready_without_eico_relationship_and_current_stock():
 e=ConversionEvidence(("buyer",),("shipment",),("400x6",),("42CrMo4-QT",),(),())
 s=state(e)
 assert s.startswith("PARTIAL_MISSING:")
 assert "stock_current_refs" in s and "eico_relationship_refs" in s
 assert shipment_to_buyer_is_eico_relationship() is False
