"""Steel merchant/buyer discovery routing for NEXUS.

Discovery signals are hypotheses until evidence adapters validate entity, role,
product fit and relationship. Scores prioritize research; they do not authorize outreach.
"""
from dataclasses import dataclass

ROLES={"PRODUCER","TRADER","STOCKIST","IMPORTER","EXPORTER","PROCESSOR","END_USER","EPC","SERVICE_CENTER","FORGE","MACHINE_SHOP","UNKNOWN"}
SIGNALS={"SHIPMENT","PROCUREMENT","CATALOG","CUSTOMER_REFERENCE","CERTIFICATE","INDUSTRIAL_APPLICATION","DIRECTORY","PROFESSIONAL_ROLE","WEBSITE","TRADE_FAIR"}

@dataclass(frozen=True)
class SteelDiscoveryCandidate:
 entity:str; role:str; signals:tuple[str,...]
 product_fit:float; demand_likelihood:float; relationship_value:float
 evidence_quality:float; recency:float; discovery_cost:float=1.0
 def validate(self):
  if self.role not in ROLES: raise ValueError("invalid_role")
  if any(x not in SIGNALS for x in self.signals): raise ValueError("invalid_signal")
  vals=(self.product_fit,self.demand_likelihood,self.relationship_value,self.evidence_quality,self.recency)
  if any(v<0 or v>1 for v in vals) or self.discovery_cost<=0: raise ValueError("invalid_score")
 def priority(self):
  self.validate()
  return self.product_fit*self.demand_likelihood*self.relationship_value*self.evidence_quality*self.recency/self.discovery_cost

def discovery_routes():
 return {
 "SHIPMENT_REVERSE":["HS7228 exporter -> named foreign buyer","buyer -> recurring supplier","shipment description -> grade/form"],
 "PROCUREMENT_REVERSE":["alloy grade -> tender buyer","failed tender -> future watch","award protocol -> supplier edge"],
 "APPLICATION_REVERSE":["gear/shaft/roll/tooling -> manufacturer","hydraulic cylinder -> rod/tube buyer","mining crusher -> shaft/forging buyer"],
 "SUPPLIER_CUSTOMER_REVERSE":["supplier customer-list -> buyer candidate","certificate/project reference -> relationship hypothesis"],
 "TRADER_GRAPH":["grade catalogue -> stockist/trader","trader brands/origins -> upstream hypothesis","warehouse/service center -> downstream buyers"],
 "PEOPLE_ROLE":["materials/procurement/supply role -> company","technical contact -> requirement intelligence"],
 "ADJACENCY":["forge/machine shop -> raw material demand","EPC/repair/MRO -> project demand","steel producer maintenance -> roll/shaft/forging demand"],
 }

def prioritize(candidates):
 return tuple(sorted(candidates,key=lambda x:(-x.priority(),x.entity)))
