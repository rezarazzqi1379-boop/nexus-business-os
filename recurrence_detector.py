"""Conservative recurrence detection for commercial/maintenance events."""
from dataclasses import dataclass
@dataclass(frozen=True)
class RecurrenceEvent:
 project_id:str; entity_id:str; asset_id:str; event_date:str; source_ref:str; origin_id:str=""
def year(e:RecurrenceEvent)->str:return e.event_date[:4]
def recurrence_state(events:tuple[RecurrenceEvent,...],project_id:str,asset_id:str)->str:
 xs=[e for e in events if e.project_id==project_id and e.asset_id==asset_id and e.source_ref and e.event_date]
 origins={e.origin_id or e.source_ref for e in xs}; years={year(e) for e in xs}
 if len(xs)<2:return "SINGLE_EVENT"
 if len(origins)<2:return "DUPLICATE_EVIDENCE"
 if len(years)<2:return "REPEATED_SAME_PERIOD"
 return "MULTI_PERIOD_PATTERN"
def may_predict_next_purchase(events,project_id,asset_id)->bool:
 # Pattern alone is insufficient for a current-demand or timing claim.
 return False
