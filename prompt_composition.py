"""Compose NEXUS prompt layers, expose conflicts, and measure versions without granting authority."""
from dataclasses import dataclass
from enum import IntEnum

class Priority(IntEnum):
 SESSION=10; ADAPTER=20; CAPABILITY=30; PROJECT=40; CANONICAL=50; ACTION_GATE=60

@dataclass(frozen=True)
class Directive:
 key:str; value:str; source:str; priority:Priority; project_id:str=""

@dataclass(frozen=True)
class Conflict:
 key:str; winner:str; loser:str; reason:str

@dataclass(frozen=True)
class PromptMetric:
 prompt_id:str; version:str; task_id:str; success:bool
 failures:int=0; cost_units:float=0.0; conversion_delta:float=0.0

def compose(ds:tuple[Directive,...],project_id:str)->tuple[dict[str,str],tuple[Conflict,...]]:
 scoped=[d for d in ds if not d.project_id or d.project_id==project_id]
 if any(d.project_id and d.project_id!=project_id and d.priority>=Priority.PROJECT for d in ds):
  raise ValueError("cross_project_directive")
 out={}; owners={}; conflicts=[]
 for d in sorted(scoped,key=lambda x:int(x.priority)):
  if d.key in out and out[d.key]!=d.value:
   prev=owners[d.key]
   if d.priority==prev.priority:
    raise ValueError("unresolved_equal_priority_conflict")
   conflicts.append(Conflict(d.key,d.source,prev.source,"higher_priority"))
  out[d.key]=d.value; owners[d.key]=d
 return out,tuple(conflicts)

def promotion_delta(candidate:tuple[PromptMetric,...],baseline:tuple[PromptMetric,...])->dict[str,float]:
 def agg(xs):
  n=max(len(xs),1); return {
   "success_rate":sum(x.success for x in xs)/n,
   "failure_rate":sum(x.failures for x in xs)/n,
   "avg_cost":sum(x.cost_units for x in xs)/n,
   "conversion":sum(x.conversion_delta for x in xs)/n}
 c,b=agg(candidate),agg(baseline)
 return {k:c[k]-b[k] for k in c}

def should_promote(candidate,baseline)->bool:
 d=promotion_delta(candidate,baseline)
 return d["success_rate"]>0 and d["failure_rate"]<=0 and d["conversion"]>=0 and d["avg_cost"]<=0
