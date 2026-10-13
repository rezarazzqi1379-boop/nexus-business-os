"""Priority queue for reverse/missing-node commercial discovery."""
from dataclasses import dataclass

@dataclass(frozen=True)
class DiscoveryTask:
 task_id:str; question:str; path:str
 expected_value:float; strategic_importance:float; evidence_gap:float; novelty_probability:float; information_value:float; expected_cost:float
 def priority(self)->float:
  vals=(self.expected_value,self.strategic_importance,self.evidence_gap,self.novelty_probability,self.information_value)
  if any(v<0 for v in vals) or self.expected_cost<=0:raise ValueError("invalid_priority_inputs")
  return self.expected_value*self.strategic_importance*self.evidence_gap*self.novelty_probability*self.information_value/self.expected_cost

def prioritize(tasks):
 return tuple(sorted(tasks,key=lambda x:(-x.priority(),x.task_id)))

def missing_node_tasks(*,source_id:str,target_id:str,relation:str,prefix:str="chain")->tuple[DiscoveryTask,...]:
 qs=(
  ("UPSTREAM",f"Who supplied {source_id} before {relation}?"),
  ("INTERMEDIATE",f"What commercial actor is missing between {source_id} and {target_id}?"),
  ("DOWNSTREAM",f"Who consumed or bought from {target_id} after {relation}?"),
  ("FALSIFICATION",f"What evidence would disprove {source_id} {relation} {target_id}?"),
 )
 return tuple(DiscoveryTask(f"{prefix}-{i+1}",q,p,1,1,1,1,1,1) for i,(p,q) in enumerate(qs))
