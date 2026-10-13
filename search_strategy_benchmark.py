"""Equal-budget strategy benchmark for commercial discovery."""
from dataclasses import dataclass

@dataclass(frozen=True)
class SearchStrategyResult:
 name:str; attempts:int; sources:int; qualified_demands:int; named_buyers:int; verified_relationships:int; false_edges_prevented:int; technical_fit_opportunities:int; information_gain:float; cost:float; latency_seconds:float; resolved_high_value_nodes:int
 def validate(self):
  ints=(self.attempts,self.sources,self.qualified_demands,self.named_buyers,self.verified_relationships,self.false_edges_prevented,self.technical_fit_opportunities,self.resolved_high_value_nodes)
  if any(type(x) is not int or x<0 for x in ints) or self.cost<0 or self.latency_seconds<0 or self.information_gain<0:raise ValueError("invalid_result")

def compare_equal_budget(xs):
 for x in xs:x.validate()
 if not xs:return {"comparable":False}
 budget={(x.attempts,x.sources) for x in xs}
 if len(budget)!=1:return {"comparable":False,"reason":"unequal_query_or_source_budget"}
 return {"comparable":True,"results":{x.name:{"qualified_demands_per_search":x.qualified_demands/x.attempts if x.attempts else None,"verified_relationships_per_search":x.verified_relationships/x.attempts if x.attempts else None,"information_gain_per_search":x.information_gain/x.attempts if x.attempts else None,"resolution_yield":x.resolved_high_value_nodes/x.attempts if x.attempts else None} for x in xs}}
