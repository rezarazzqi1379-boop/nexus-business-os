"""Generate multiple independent buyer-discovery paths without claiming they succeeded."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DiscoveryPath:
 path_id:str; steps:tuple[str,...]; status:str="PLANNED"
def generate_paths(product:str,application:str,country:str):
 if not all(x.strip() for x in (product,application,country)):raise ValueError("product_application_country_required")
 base=f"{country}:{application}:{product}"
 return (
  DiscoveryPath(base+":application",(application,"COMPANY","PLANT","BUYER")),
  DiscoveryPath(base+":trade",("HS_CANDIDATE","TRADE_FLOW","COMPANY",application,"BUYER")),
  DiscoveryPath(base+":competitor",("COMPETITOR","MARKET","CUSTOMER_HYPOTHESIS",application,"BUYER")),
  DiscoveryPath(base+":project",("PROJECT","EQUIPMENT","COMPONENT",product,"BUYER")),
  DiscoveryPath(base+":signal",("DEMAND_SIGNAL","COMPANY","POTENTIAL_NEED",product,"BUYER")),
 )
