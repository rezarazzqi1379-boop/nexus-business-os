from demand_trigger_engine import *
def test_trigger_never_auto_qualifies():
 t=DemandTrigger("buyer","TENDER",("e1",),"2026-10-07")
 assert trigger_state(t)=="INVESTIGATE"
 assert qualifies_opportunity(t) is False
def test_trigger_requires_evidence():
 try:
  trigger_state(DemandTrigger("buyer","RFQ",(),"2026-10-07")); assert False
 except ValueError: assert True
