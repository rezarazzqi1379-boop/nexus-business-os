from commercial_chain_graph import *

def test_verified_edge_requires_independent_evidence():
 e=candidate_edge(source_id="supplier",relation="SUPPLIED_TO",target_id="buyer",evidence_refs=("a",),source_families=("same",))
 assert promote_verified(e).state=="CANDIDATE"
 e2=candidate_edge(source_id="supplier",relation="SUPPLIED_TO",target_id="buyer",evidence_refs=("a","b"),source_families=("official","customs"))
 assert promote_verified(e2).state=="VERIFIED"

def test_unresolved_contradiction_blocks_verified():
 e=ChainEdge("a","BOUGHT","b","CANDIDATE",("x","y"),None,("official","independent"),("contra",))
 assert promote_verified(e).state=="CANDIDATE"

def test_aggregate_trade_never_names_company_buyer():
 e=infer_company_edge_from_aggregate_trade(country="Belarus",product="HS722830")
 assert e.state=="HYPOTHESIS" and e.relation=="AGGREGATE_TRADE_SIGNAL"

def test_reverse_expansion_produces_questions_not_edges():
 e=ChainEdge("mine","SOLD","mill")
 q=expansion_questions(e)
 assert len(q)==4 and all(isinstance(x,str) for x in q)
