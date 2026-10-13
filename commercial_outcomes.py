"""Aggregate evidence-backed historical outcomes for Commercial Genome."""
from collections import Counter
from commercial_genome import comparable
def outcome_summary(target,history,minimum_similarity=.5):
 matches=comparable(target,history,minimum_similarity)
 counts=Counter(); usable=[]
 for score,g in matches:
  if g.outcome=="UNKNOWN" or not g.outcome_evidence_refs:continue
  counts[g.outcome]+=1; usable.append((score,g.opportunity_id))
 return {"comparable_cases":len(usable),"outcomes":dict(sorted(counts.items())),"matches":tuple(usable)}


def benchmark_interpretation(*,cohort_bound=False,time_window_bound=False,search_budget_bound=False,source_budget_bound=False,stage_exposure_bound=False):
 """Outcome summaries are descriptive unless all exposure controls are explicit."""
 return "CAUSAL_COMPARISON_READY" if all((cohort_bound,time_window_bound,search_budget_bound,source_budget_bound,stage_exposure_bound)) else "DESCRIPTIVE_ONLY"
