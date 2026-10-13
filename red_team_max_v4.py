"""RED TEAM MAX v4 adversarial guards for evidence-native commercial decisions."""
from dataclasses import dataclass

@dataclass(frozen=True)
class DurableFeature:
    value:str
    evidence_refs:tuple[str,...]
    observed_at:str
    contradicted:bool=False
    stale:bool=False

def similarity_eligible(f:DurableFeature)->bool:
    return bool(f.value.strip() and f.evidence_refs and f.observed_at.strip() and not f.contradicted and not f.stale)

@dataclass(frozen=True)
class DistillationCase:
    case_id:str
    source_family:str
    evidence_refs:tuple[str,...]

def independent_distillation(cases, *, minimum_cases:int=3, minimum_source_families:int=2)->bool:
    xs=tuple(cases)
    ids={x.case_id for x in xs if x.case_id.strip()}
    families={x.source_family for x in xs if x.source_family.strip()}
    return len(ids)>=minimum_cases and len(families)>=minimum_source_families and all(x.evidence_refs for x in xs)

def causal_benchmark_ready(*, cohort_bound:bool,time_window_bound:bool,search_budget_bound:bool,source_budget_bound:bool,stage_exposure_bound:bool)->bool:
    return all((cohort_bound,time_window_bound,search_budget_bound,source_budget_bound,stage_exposure_bound))
