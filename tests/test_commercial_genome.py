from commercial_genome import CommercialGenome,similarity,comparable,validate_genome
def g(i,app,product,outcome="UNKNOWN",refs=()):
 return CommercialGenome(i,{"application":(app,),"product":(product,),"market":("Turkey",)},outcome,refs)
def test_similarity_is_deterministic_and_explainable():
 assert similarity(g("A","gear","20MnCr5"),g("B","gear","20MnCr5"))==1.0
 assert similarity(g("A","gear","20MnCr5"),g("C","shaft","42CrMo4"))==.3333
def test_historical_outcome_requires_evidence():
 assert "outcome_requires_evidence" in validate_genome(g("W","gear","20MnCr5","WON"))
def test_comparables_are_ranked():
 assert comparable(g("A","gear","20MnCr5"),[g("C","shaft","42CrMo4"),g("B","gear","20MnCr5")])[0][1].opportunity_id=="B"
