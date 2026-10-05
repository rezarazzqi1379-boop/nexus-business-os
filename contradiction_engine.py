"""Keep support, contradiction and absence distinct."""
STATES={"SUPPORTING","NEGATIVE_EVIDENCE","CONTRADICTORY_EVIDENCE","STALE_EVIDENCE","SOURCE_UNAVAILABLE","NO_EVIDENCE","NOT_CHECKED"}
def claim_state(*,checked:bool,support_refs=(),contradiction_refs=(),negative_refs=()):
 if not checked:return "NOT_CHECKED"
 if contradiction_refs:return "CONTRADICTORY_EVIDENCE"
 if negative_refs:return "NEGATIVE_EVIDENCE"
 if support_refs:return "SUPPORTING"
 return "NO_EVIDENCE"
