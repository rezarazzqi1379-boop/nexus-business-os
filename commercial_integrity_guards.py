"""Conservative commercial guards for price comparability, grade equivalence and entity merge."""
from dataclasses import dataclass

@dataclass(frozen=True)
class PriceObservation:
 product:str; grade:str; dimension:str; condition:str; quantity:float|None; incoterm:str; currency:str; unit:str; price_type:str

def price_comparability(a:PriceObservation,b:PriceObservation)->str:
 if "UNKNOWN" in {a.price_type,b.price_type}: return "LOW"
 if {a.price_type,b.price_type} & {"CUSTOMS_UNIT_VALUE"} and a.price_type!=b.price_type:return "NOT_DIRECTLY_COMPARABLE"
 critical=(a.product==b.product,a.grade==b.grade,a.dimension==b.dimension,a.condition==b.condition,a.currency==b.currency,a.unit==b.unit,a.incoterm==b.incoterm)
 if not all(critical):return "LOW"
 if a.quantity is None or b.quantity is None:return "MEDIUM"
 ratio=max(a.quantity,b.quantity)/max(min(a.quantity,b.quantity),1e-12)
 return "HIGH" if ratio<=1.25 else "MEDIUM"

def grade_equivalence(*,standard_a:str,standard_b:str,chemistry_compared:bool,mechanicals_compared:bool,heat_treatment_compared:bool,delivery_condition_compared:bool,mtc_evidence:bool)->str:
 if standard_a==standard_b and all((chemistry_compared,mechanicals_compared,heat_treatment_compared,delivery_condition_compared)):return "SUPPORTED_SAME_STANDARD"
 if all((chemistry_compared,mechanicals_compared,heat_treatment_compared,delivery_condition_compared,mtc_evidence)):return "SUPPORTED_EQUIVALENCE"
 return "CANDIDATE_EQUIVALENCE"

def entity_merge_decision(*,canonical_domain_same:bool,legal_identifier_same:bool,alias_only:bool,subsidiary_possible:bool)->str:
 if legal_identifier_same:return "MERGE"
 if canonical_domain_same and not subsidiary_possible:return "MERGE_WITH_REVIEW"
 if alias_only or subsidiary_possible:return "REQUIRE_RESOLUTION"
 return "KEEP_SEPARATE"
