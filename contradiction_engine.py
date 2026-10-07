"""Preserve support, contradiction, negative evidence and authority resolution without deletion."""
from dataclasses import dataclass
STATES={"SUPPORTING","NEGATIVE_EVIDENCE","CONTRADICTORY_EVIDENCE","STALE_EVIDENCE","SOURCE_UNAVAILABLE","NO_EVIDENCE","NOT_CHECKED"}
def claim_state(*,checked:bool,support_refs=(),contradiction_refs=(),negative_refs=()):
 if not checked:return "NOT_CHECKED"
 if contradiction_refs:return "CONTRADICTORY_EVIDENCE"
 if negative_refs:return "NEGATIVE_EVIDENCE"
 if support_refs:return "SUPPORTING"
 return "NO_EVIDENCE"
@dataclass(frozen=True)
class ClaimValue:
 value:str; source_id:str; authority:int; observed_at:str
def resolve_values(values:list[ClaimValue])->str:
 if not values:return "UNKNOWN"
 uniq={v.value for v in values}
 if len(uniq)==1:return "CONSISTENT"
 top=max(v.authority for v in values); winners={v.value for v in values if v.authority==top}
 return "AUTHORITY_RESOLVED_WITH_CONTRADICTION" if len(winners)==1 else "UNRESOLVED_CONTRADICTION"
