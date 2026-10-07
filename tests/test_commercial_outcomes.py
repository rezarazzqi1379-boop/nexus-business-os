from commercial_genome import GenomeFeature,CommercialGenome
from commercial_outcomes import outcome_summary
def feat(d,v): return GenomeFeature(d,v,(f"e:{d}:{v}",),"2026-10-05")
def g(i,outcome,refs=()):
 return CommercialGenome(i,(feat("application","gear"),feat("product","20MnCr5"),feat("market","Turkey")),outcome,refs)
def test_summary_uses_only_evidenced_known_outcomes():
 s=outcome_summary(g("T","UNKNOWN"),[g("1","WON",("e:1",)),g("2","LOST",("e:2",)),g("3","UNKNOWN"),g("4","RFQ",("e:4",))])
 assert s["comparable_cases"]==3
 assert s["outcomes"]=={"LOST":1,"RFQ":1,"WON":1}


def test_outcome_benchmark_is_descriptive_without_exposure_controls():
 assert benchmark_interpretation()=="DESCRIPTIVE_ONLY"
 assert benchmark_interpretation(cohort_bound=True,time_window_bound=True,search_budget_bound=True,source_budget_bound=True,stage_exposure_bound=True)=="CAUSAL_COMPARISON_READY"
