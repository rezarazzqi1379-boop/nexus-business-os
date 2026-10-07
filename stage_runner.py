"""Select the smallest NEXUS stage that attacks the current measured blocker."""
ORDER=("RECOVERY","CLUE_INGEST","ENTITY_RESOLUTION","THREAD_FUSION","HYPOTHESIS","PRIMARY_DOCUMENT","TECHNICAL","COMMERCIAL_GRAPH","STOCK","ELIGIBILITY","CONVERSION","RED_TEAM","SOURCE_ROI","PERSISTENCE","LEARNING","ACTION_GATE")

def next_stage(*,recovery_ok:bool,primary_docs_ok:bool,technical_ok:bool,stock_ok:bool,eligibility_ok:bool,relationship_ok:bool,evidence_ready:bool,protected_action_requested:bool=False)->str:
 if not recovery_ok:return "RECOVERY"
 if not primary_docs_ok:return "PRIMARY_DOCUMENT"
 if not technical_ok:return "TECHNICAL"
 if not stock_ok:return "STOCK"
 if not eligibility_ok:return "ELIGIBILITY"
 if not relationship_ok:return "COMMERCIAL_GRAPH"
 if not evidence_ready:return "CONVERSION"
 return "ACTION_GATE" if protected_action_requested else "RED_TEAM"

def capability_review_stage(*, measured_repeated_bottleneck:bool, acceptance_test_defined:bool)->str:
 """Capability expansion is evaluated only after a measured bottleneck exists."""
 if not measured_repeated_bottleneck:
  return "NO_CAPABILITY_EXPANSION"
 if not acceptance_test_defined:
  return "LEARNING"
 return "SOURCE_ROI"
