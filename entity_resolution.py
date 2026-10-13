"""Conservative entity resolution. Similar names generate review candidates, not merges."""
from dataclasses import dataclass
@dataclass(frozen=True)
class IdentityEvidence:
 legal_id_match:bool=False; domain_match:bool=False; official_source_match:bool=False; name_similarity:float=0.0
def resolution_state(e:IdentityEvidence)->str:
 if e.legal_id_match:return "RESOLVED_STRONG"
 if e.domain_match and e.official_source_match:return "RESOLVED_CORROBORATED"
 if e.name_similarity>=0.85:return "REVIEW_POSSIBLE_ALIAS"
 return "DISTINCT_OR_UNKNOWN"
