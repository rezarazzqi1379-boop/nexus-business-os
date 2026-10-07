import pytest
from commercial_outcome_adapter import build_funnel
from deal_room import DealRoom
from commercial_genome import CommercialGenome

def d(i,stage,refs=("crm:1",)):
 return DealRoom(i,stage,refs,next_action="" if stage in {"WON","LOST"} else "next")

def test_deal_rooms_feed_measured_funnel_and_cost():
 xs=(d("a","PROSPECT"),d("b","QUALIFIED"),d("c","RFQ"),d("d","ORDER"))
 r=build_funnel(xs,total_cost_usd=40)
 f=r["funnel"]
 assert (f.discovered,f.qualified,f.rfqs,f.orders)==(4,3,2,1)
 assert r["cost_metrics"]["cost_per_order"]==40.0
 assert f.outcome_evidence_refs==("crm:1",)

def test_outcome_specific_genome_evidence_is_preserved():
 g=CommercialGenome("a",(),outcome="RFQ",outcome_evidence_refs=("rfq:mail-1",))
 r=build_funnel((d("a","RFQ",("deal:1",)),),(g,))
 assert set(r["outcome_evidence_refs"])=={"deal:1","rfq:mail-1"}

def test_invalid_advanced_deal_cannot_create_outcome():
 bad=DealRoom("x","RFQ",(),next_action="follow")
 with pytest.raises(ValueError,match="invalid_deal_room"):
  build_funnel((bad,))
