"""NEXUS outcome manager: prioritize verified bottlenecks, not activity."""
from dataclasses import dataclass
from enum import Enum

class OutcomeState(str,Enum):
 RESEARCH="RESEARCH"; VERIFY="VERIFY"; BUILD="BUILD"; TEST="TEST"; GATED="GATED"; BLOCKED="BLOCKED"; READY="READY"

@dataclass(frozen=True)
class Outcome:
 outcome_id:str; project_id:str; objective:str; bottleneck:str
 evidence_strength:float; expected_value:float; conversion_lift:float
 cost:float; risk:float; critical_unknowns:int=0
 protected_action:bool=False; contradiction:bool=False

def valid01(x:float)->bool: return 0<=x<=1

def state(o:Outcome)->OutcomeState:
 if o.contradiction: return OutcomeState.BLOCKED
 if o.protected_action: return OutcomeState.GATED
 if o.critical_unknowns>0: return OutcomeState.VERIFY
 if o.evidence_strength<0.5: return OutcomeState.RESEARCH
 return OutcomeState.READY

def priority(o:Outcome)->float:
 if not all(valid01(x) for x in (o.evidence_strength,o.expected_value,o.conversion_lift,o.cost,o.risk)):
  raise ValueError("metric_out_of_range")
 if state(o) in {OutcomeState.BLOCKED,OutcomeState.GATED}: return -1
 return round((o.evidence_strength*o.expected_value*max(o.conversion_lift,.05))/(1+o.cost+o.risk),6)

def rank_outcomes(xs:tuple[Outcome,...])->tuple[Outcome,...]:
 ids=[x.outcome_id for x in xs]
 if len(ids)!=len(set(ids)): raise ValueError("duplicate_outcome")
 return tuple(sorted(xs,key=lambda x:(priority(x),x.outcome_id),reverse=True))
