"""Minimal explicit conflict state for evidence-backed scalar procurement fields."""
from dataclasses import dataclass

STATES={"CONSISTENT","CONFLICTED","RESOLVED"}

@dataclass(frozen=True)
class ScalarObservation:
 value:float
 evidence_ref:str
 source_class:str
 primary:bool=False

def resolve_scalar(observations:tuple[ScalarObservation,...])->dict:
 if not observations:return {"state":"CONFLICTED","supported_value":None,"contradictions":()}
 values={x.value for x in observations}
 if len(values)==1:return {"state":"CONSISTENT","supported_value":observations[0].value,"contradictions":()}
 primary_values={x.value for x in observations if x.primary}
 if len(primary_values)==1:
  v=next(iter(primary_values))
  return {"state":"RESOLVED","supported_value":v,"contradictions":tuple(x for x in observations if x.value!=v)}
 return {"state":"CONFLICTED","supported_value":None,"contradictions":observations}
