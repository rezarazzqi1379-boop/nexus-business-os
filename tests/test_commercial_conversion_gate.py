from commercial_conversion_gate import *
def test_application_product_is_not_conversion():
 e=ConversionEvidence("AZINFORGE",technical_refs=("official:product",))
 assert conversion_state(e)=="INSUFFICIENT_BINDING"
 assert verified_commercial_conversion(e) is False
def test_relationship_without_current_demand_is_not_conversion():
 e=ConversionEvidence("GUNES",relationship_refs=("shipment:historical",),technical_refs=("product:steel",))
 assert conversion_state(e)=="RELATIONSHIP_TECHNICAL_ONLY"
 assert verified_commercial_conversion(e) is False
def test_full_binding_can_be_evidence_ready():
 e=ConversionEvidence("BUYER",("rel",),("demand",),("tech",),("current",))
 assert verified_commercial_conversion(e) is True
