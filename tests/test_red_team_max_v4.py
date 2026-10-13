from red_team_max_v4 import *

def test_stale_or_contradicted_genome_feature_not_similarity_eligible():
    assert similarity_eligible(DurableFeature("gear",("r",),"2026-01-01",stale=True)) is False
    assert similarity_eligible(DurableFeature("gear",("r",),"2026-01-01",contradicted=True)) is False

def test_three_duplicate_cases_do_not_distill():
    xs=[DistillationCase("same","web",("r1",)) for _ in range(3)]
    assert independent_distillation(xs) is False

def test_three_independent_cases_across_sources_can_distill():
    xs=[DistillationCase("a","trade",("a",)),DistillationCase("b","tender",("b",)),DistillationCase("c","trade",("c",))]
    assert independent_distillation(xs) is True

def test_outcome_counts_not_causal_without_exposure_controls():
    assert causal_benchmark_ready(cohort_bound=True,time_window_bound=True,search_budget_bound=False,source_budget_bound=True,stage_exposure_bound=True) is False
