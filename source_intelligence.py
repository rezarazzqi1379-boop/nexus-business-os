"""Evidence-source ranking for commercial discovery. Authority and yield are separate."""
from dataclasses import dataclass
@dataclass(frozen=True)
class SourceScore:
 authority:int; freshness:int; reproducibility:int; unique_qualified_hits:int; raw_hits:int; cost:int
def precision(s:SourceScore)->float:
 return s.unique_qualified_hits/s.raw_hits if s.raw_hits>0 else 0.0
def source_state(s:SourceScore)->str:
 if min(s.authority,s.freshness,s.reproducibility)<0:return "INVALID"
 if s.raw_hits>0 and s.unique_qualified_hits==0:return "DOWNGRADE_ZERO_QUALIFIED_YIELD"
 if s.authority<2:return "DISCOVERY_ONLY_LOW_AUTHORITY"
 if s.freshness<2:return "HISTORICAL_ONLY"
 if s.reproducibility<2:return "CLAIM_REVALIDATION"
 if s.cost>max(1,s.unique_qualified_hits*2):return "HOLD_COST"
 return "PRIMARY_OR_VERIFIED_DISCOVERY"
