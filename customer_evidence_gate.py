"""Evidence gate for converting sector/application claims into named customer hypotheses."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CustomerClaim:
 supplier:str
 customer:str
 sector_claim_refs:tuple[str,...]=()
 relationship_refs:tuple[str,...]=()
 demand_refs:tuple[str,...]=()

def customer_state(c:CustomerClaim)->str:
 if not c.supplier.strip() or not c.customer.strip(): raise ValueError("entities_required")
 if c.relationship_refs and c.demand_refs: return "QUALIFIED_RELATIONSHIP_DEMAND"
 if c.relationship_refs: return "RELATIONSHIP_BOUND"
 if c.sector_claim_refs: return "UNBOUND_SECTOR_HYPOTHESIS"
 return "UNSUPPORTED"

def can_promote_named_customer(c:CustomerClaim)->bool:
 return bool(c.relationship_refs)
