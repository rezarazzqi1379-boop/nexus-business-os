from trade_recurrence_gate import *
def test_duplicate_renderings_are_one_observation():
 r=TradeObservation("Buyer","2026-01-29","722840","1978","42CrMo4|400|6m")
 assert recurrence_state([r,r,r])=="ONE_OBSERVED"
def test_distinct_dates_can_establish_recurrence():
 a=TradeObservation("Buyer","2026-01-29","722840","1978","42CrMo4|400|6m")
 b=TradeObservation("Buyer","2026-03-01","722840","2100","42CrMo4|400|6m")
 assert recurrence_state([a,b])=="RECURRENT"
