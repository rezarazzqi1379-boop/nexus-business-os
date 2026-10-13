"""Demand reconstruction without converting engineering inference into purchase evidence."""
from dataclasses import dataclass

CLASSES={"RAW_BAR","FORGING","ROLLED_BAR","TUBE","CHROME_ROD","MACHINED_COMPONENT","FASTENER","GEAR","SHAFT","TOOLING","OTHER"}
STATES={"OBSERVED","INFERRED","UNKNOWN"}

@dataclass(frozen=True)
class DemandSignal:
 buyer:str; demand_class:str; description:str; evidence_refs:tuple[str,...]
 grade:str=""; quantity:float|None=None; quantity_unit:str=""; state:str="OBSERVED"
 def validate(self):
  if not self.buyer.strip() or self.demand_class not in CLASSES or not self.description.strip() or not self.evidence_refs:raise ValueError("invalid_demand")
  if self.state not in STATES or (self.quantity is not None and self.quantity<=0):raise ValueError("invalid_demand")

def infer_upstream(signal:DemandSignal,*,input_form:str,reason:str)->dict:
 signal.validate()
 if not input_form.strip() or not reason.strip():raise ValueError("inference_basis_required")
 return {"buyer":signal.buyer,"input_form":input_form,"state":"HYPOTHESIS","reason":reason,"purchase_evidence":False}
