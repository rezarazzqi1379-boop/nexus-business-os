"""Discovery miss taxonomy for regression distillation."""
REASONS={"SOURCE_GAP","QUERY_GAP","LANGUAGE_GAP","ONTOLOGY_GAP","TRADE_DATA_GAP","APPLICATION_MAPPING_GAP","ENTITY_RESOLUTION_FAILURE","DEDUP_FAILURE","STALE_EVIDENCE","BAD_SCORING","FALSE_NEGATIVE","PROVIDER_FAILURE","COST_GATE","COMPLIANCE_FILTER","UNKNOWN"}
from dataclasses import dataclass
@dataclass(frozen=True)
class DiscoveryFailure:
 case_id:str; reason:str; evidence_refs:tuple[str,...]=()
def validate_failure(x):
 e=[]
 if not x.case_id.strip():e.append("case_id_required")
 if x.reason not in REASONS:e.append("invalid_reason")
 if x.reason!="UNKNOWN" and not x.evidence_refs:e.append("specific_failure_requires_evidence")
 return tuple(e)
