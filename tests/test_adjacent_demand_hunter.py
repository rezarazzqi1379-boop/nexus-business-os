from adjacent_demand_hunter import *
def test_adjacent_grade_stays_dna_only():
    x=AdjacentDemand("BHEL","34CrMo4",180,2000,False)
    assert route(x,capability_min=120,capability_max=1600,exact_grade=False)=="ADJACENT_GRADE_DNA_ONLY"
def test_current_exact_grade_is_review_only():
    x=AdjacentDemand("Buyer","42CrMo4",180,2000,True)
    assert route(x,capability_min=120,capability_max=1600,exact_grade=True)=="EXACT_GRADE_CURRENT_REVIEW"
