"""Discover adjacent demand without converting adjacency into technical fit."""
from dataclasses import dataclass
@dataclass(frozen=True)
class AdjacentDemand:
 buyer:str; grade:str; diameter_mm:float; length_mm:float; current_open:bool
def route(x:AdjacentDemand, *, capability_min:float, capability_max:float, exact_grade:bool)->str:
 if not x.buyer.strip() or not x.grade.strip(): return "REJECT_INCOMPLETE"
 if not (capability_min <= x.diameter_mm <= capability_max): return "OUTSIDE_GEOMETRY_CAPABILITY"
 if exact_grade and x.current_open:return "EXACT_GRADE_CURRENT_REVIEW"
 if exact_grade:return "HISTORICAL_EXACT_GRADE_DNA"
 return "ADJACENT_GRADE_DNA_ONLY"
