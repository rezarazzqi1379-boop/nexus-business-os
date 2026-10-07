from customer_evidence_gate import *
def test_sector_claim_cannot_promote_named_customer():
 c=CustomerClaim("GUNES","MINING_CO",("official:sectors",),(),())
 assert customer_state(c)=="UNBOUND_SECTOR_HYPOTHESIS"
 assert can_promote_named_customer(c) is False
def test_relationship_evidence_can_bind_customer():
 c=CustomerClaim("GUNES","BUYER",(),("shipment:1",),())
 assert customer_state(c)=="RELATIONSHIP_BOUND"
 assert can_promote_named_customer(c) is True
