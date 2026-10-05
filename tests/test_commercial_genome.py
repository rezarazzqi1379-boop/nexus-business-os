from commercial_genome import GenomeFeature,CommercialGenome,similarity,comparable,validate_genome
def f(d,v): return GenomeFeature(d,v,(f"e:{d}:{v}",),"2026-10-05")
def g(i,app,product,outcome="UNKNOWN",refs=()):
 return CommercialGenome(i,(f("application",app),f("product",product),f("market","Turkey")),outcome,refs)
def test_similarity_is_deterministic_and_explainable():
 assert similarity(g("A","gear","20MnCr5"),g("B","gear","20MnCr5"))==1.0
 assert similarity(g("A","gear","20MnCr5"),g("C","shaft","42CrMo4"))==.3333
def test_feature_and_historical_outcome_require_evidence():
 assert "feature_evidence_required" in validate_genome(CommercialGenome("X",(GenomeFeature("application","gear",(),"2026-10-05"),)))
 assert "outcome_requires_evidence" in validate_genome(g("W","gear","20MnCr5","WON"))
def test_comparables_are_ranked_and_need_shared_dimensions():
 assert comparable(g("A","gear","20MnCr5"),[g("C","shaft","42CrMo4"),g("B","gear","20MnCr5")])[0][1].opportunity_id=="B"
