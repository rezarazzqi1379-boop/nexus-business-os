from inventory_matcher import *
def test_undated_snapshot_requires_reconfirmation():
 l=StockLot("42CrMo4",290,760,2,7,80)
 assert match_state(l,"42CrMo4",300,5)=="SNAPSHOT_MATCH_RECONFIRM_STOCK"
 assert can_quote_as_available(l) is False
def test_dimension_outside_range_fails():
 l=StockLot("C45",290,980,2,8,156)
 assert match_state(l,"C45",200,5)=="NO_MATCH"
