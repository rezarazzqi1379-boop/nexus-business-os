"""Comparable relationship-discovery metrics for NEXUS v8."""
from dataclasses import dataclass

@dataclass(frozen=True)
class RelationshipBenchmark:
 investigated:int; verified:int; false_edges_prevented:int; named_nodes:int; actor_classes:int; demand_signals:int
 def validate(self):
  xs=(self.investigated,self.verified,self.false_edges_prevented,self.named_nodes,self.actor_classes,self.demand_signals)
  if any(type(x) is not int or x<0 for x in xs):raise ValueError("invalid_benchmark")
  if self.verified>self.investigated or self.false_edges_prevented>self.investigated:raise ValueError("invalid_relationship_counts")

def metrics(x:RelationshipBenchmark)->dict:
 x.validate()
 d=x.investigated
 return {"verified_relationship_yield":None if not d else x.verified/d,
         "false_edge_prevention_rate":None if not d else x.false_edges_prevented/d,
         "named_nodes":x.named_nodes,"actor_classes":x.actor_classes,"demand_signals":x.demand_signals}

def compare(base:RelationshipBenchmark,candidate:RelationshipBenchmark)->dict:
 b,c=metrics(base),metrics(candidate)
 comparable=base.investigated==candidate.investigated
 return {"comparable_relationship_budget":comparable,
         "verified_relationship_yield_delta":None if not comparable or b["verified_relationship_yield"] is None or c["verified_relationship_yield"] is None else c["verified_relationship_yield"]-b["verified_relationship_yield"],
         "false_edge_prevention_delta":None if not comparable or b["false_edge_prevention_rate"] is None or c["false_edge_prevention_rate"] is None else c["false_edge_prevention_rate"]-b["false_edge_prevention_rate"],
         "named_node_delta":candidate.named_nodes-base.named_nodes,
         "actor_class_delta":candidate.actor_classes-base.actor_classes,
         "demand_signal_delta":candidate.demand_signals-base.demand_signals}
