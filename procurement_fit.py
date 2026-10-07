"""Fail-closed procurement product-fit assessment."""
FIT={"EXACT_FIT","POTENTIAL_FIT","ENGINEERING_REVIEW","NO_FIT","UNKNOWN"}
FIELDS=("grade","standard","form","dimensions","heat_treatment","testing","quantity","delivery_condition")

def assess_fit(checks:dict[str,bool|None],*,equivalence_supported:bool=False)->str:
 if any(k not in checks for k in FIELDS):return "UNKNOWN"
 vals=tuple(checks[k] for k in FIELDS)
 if any(v is False for v in vals):return "NO_FIT"
 if checks["grade"] is None or checks["standard"] is None:return "UNKNOWN"
 if not equivalence_supported and checks["grade"] is not True:return "ENGINEERING_REVIEW"
 if all(v is True for v in vals):return "EXACT_FIT"
 if any(v is None for v in vals):return "ENGINEERING_REVIEW"
 return "POTENTIAL_FIT"
