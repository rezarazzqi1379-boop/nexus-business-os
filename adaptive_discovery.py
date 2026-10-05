"""Adaptive extension of reverse discovery prioritization."""
from dataclasses import dataclass
from reverse_discovery_queue import DiscoveryTask

@dataclass(frozen=True)
class AdaptiveTask:
 base:DiscoveryTask; resolution_probability:float; recency:float; product_fit:float
 queries:int=0; sources_checked:int=0; new_evidence:int=0; resolved_nodes:int=0; verified_relationships:int=0; qualified_demand:int=0
 def priority(self)->float:
  vals=(self.resolution_probability,self.recency,self.product_fit)
  if any(v<0 for v in vals):raise ValueError("invalid_adaptive_inputs")
  return self.base.priority()*self.resolution_probability*self.recency*self.product_fit
 def marginal_information_gain(self)->float|None:
  if self.queries<=0:return None
  return (self.new_evidence+self.resolved_nodes+self.verified_relationships+self.qualified_demand)/self.queries
 def state(self,threshold:float=.25)->str:
  g=self.marginal_information_gain()
  return "PAUSED_LOW_INFORMATION_GAIN" if g is not None and g<threshold else "ACTIVE"

def prioritize_adaptive(tasks):
 return tuple(sorted(tasks,key=lambda x:(-x.priority(),x.base.task_id)))
