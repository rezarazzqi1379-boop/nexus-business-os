from commercial_chain_graph import infer_company_edge_from_aggregate_trade,ChainEdge,promote_verified

def test_aggregate_trade_signal_cannot_become_named_buyer():
 e=infer_company_edge_from_aggregate_trade(country="Belarus",product="HS722830")
 assert e.relation=="AGGREGATE_TRADE_SIGNAL" and e.state=="HYPOTHESIS"
 assert e.target_id=="HS722830"

def test_false_supplier_buyer_attribution_requires_independent_evidence():
 e=ChainEdge("unknown_china_exporter","SUPPLIED_TO","unknown_belarus_buyer","CANDIDATE",("aggregate:wits",),source_families=("wits",))
 assert promote_verified(e).state=="CANDIDATE"
