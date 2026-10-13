"""Fail-closed sales readiness for procurement opportunities."""
STATES={"READY","PARTIAL","BLOCKED","UNKNOWN"}
DIMENSIONS=("TECHNICAL","COMMERCIAL","COMPLIANCE","CONTACT")

def overall_readiness(values:dict[str,str])->str:
 if set(values)!=set(DIMENSIONS) or any(v not in STATES for v in values.values()):raise ValueError("invalid_readiness")
 if any(v=="BLOCKED" for v in values.values()):return "BLOCKED"
 if any(v=="UNKNOWN" for v in values.values()):return "UNKNOWN"
 if all(v=="READY" for v in values.values()):return "READY"
 return "PARTIAL"
