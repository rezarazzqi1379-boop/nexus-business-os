"""Temporal truth: observation time never silently refreshes event validity."""
from dataclasses import dataclass
@dataclass(frozen=True)
class TemporalFact:
 event_at:str; observed_at:str; valid_from:str=""; valid_to:str=""; superseded_by:str=""
def temporal_state(x:TemporalFact, *, as_of:str)->str:
 if x.superseded_by:return "SUPERSEDED"
 if x.valid_to and as_of>x.valid_to:return "EXPIRED"
 if x.valid_from and as_of<x.valid_from:return "NOT_YET_VALID"
 return "VALID_AT_AS_OF" if x.event_at else "OBSERVATION_ONLY"
