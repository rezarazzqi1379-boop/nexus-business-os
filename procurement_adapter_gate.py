"""Benchmark gate for adding procurement data adapters."""
from dataclasses import dataclass
@dataclass(frozen=True)
class AdapterEvidence:
 target_publishers:int; ocds_publishers:int; unique_qualified_hits:int; baseline_unique_hits:int; maintenance_cost:int
def adapter_decision(x:AdapterEvidence)->str:
 if x.target_publishers<=0 or x.ocds_publishers<=0:return "HOLD_NO_DATA_COVERAGE"
 coverage=x.ocds_publishers/x.target_publishers
 gain=x.unique_qualified_hits-x.baseline_unique_hits
 if coverage<0.25:return "HOLD_LOW_COVERAGE"
 if gain<=0:return "HOLD_NO_INCREMENTAL_VALUE"
 if x.maintenance_cost>gain:return "HOLD_COST_EXCEEDS_GAIN"
 return "PILOT_JUSTIFIED"
