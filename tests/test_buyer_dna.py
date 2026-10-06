from buyer_dna import *

def test_similarity_never_qualifies():
 a=BuyerDNA("a",frozenset({"TRADER"}),frozenset({"FORGED_BAR"}),frozenset({"7228"}),frozenset(),frozenset({"TR"}),("e1",))
 b=BuyerDNA("b",frozenset({"TRADER"}),frozenset({"FORGED_BAR"}),frozenset({"7228"}),frozenset(),frozenset({"TR"}),("e2",))
 assert similarity(a,b)["score"]==1
 assert similarity(a,b)["state"]=="CANDIDATE_LOOKALIKE"
 assert qualified_by_similarity(a,b) is False

def test_missing_dimensions_do_not_create_false_match():
 a=BuyerDNA("a",frozenset(),frozenset(),frozenset(),frozenset(),frozenset(),("e1",))
 b=BuyerDNA("b",frozenset(),frozenset(),frozenset(),frozenset(),frozenset(),("e2",))
 assert similarity(a,b)["score"]==0
