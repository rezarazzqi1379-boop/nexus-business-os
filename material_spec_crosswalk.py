"""Strict material-spec crosswalk: family similarity is never equivalence."""
def spec_crosswalk(*, demanded_standard:str, evidenced_standard:str, exact_equivalence_source:bool)->str:
 if not demanded_standard.strip() or not evidenced_standard.strip(): return "UNKNOWN_STANDARD"
 if demanded_standard.casefold()==evidenced_standard.casefold(): return "EXACT_STANDARD_MATCH"
 if exact_equivalence_source: return "SOURCE_BACKED_EQUIVALENCE"
 return "NO_EQUIVALENCE_PROVEN"
def acceptance_ready(*, spec_state:str, condition_verified:bool, ndt_verified:bool, certificate_verified:bool)->bool:
 return spec_state in {"EXACT_STANDARD_MATCH","SOURCE_BACKED_EQUIVALENCE"} and condition_verified and ndt_verified and certificate_verified
