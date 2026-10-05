"""Validation for evidence-native country lead records."""
from __future__ import annotations
ALLOWED_ROLES={"END_USER","BUYER","IMPORTER","DISTRIBUTOR","COMPETITOR","STRATEGIC_PARTNER","UNKNOWN"}
ALLOWED_EVIDENCE={"OFFICIAL_COMPANY","OFFICIAL_CUSTOMS","TRADE_DATA","STANDARD","REGULATOR","INDEPENDENT","CLAIM"}
def validate_lead(r:dict)->tuple[str,...]:
    errors=[]
    for k in ("lead_id","country","company","role","applications","grade_candidates","evidence","status"):
        if k not in r: errors.append(f"missing:{k}")
    if r.get("role") not in ALLOWED_ROLES: errors.append("invalid_role")
    ev=r.get("evidence",[])
    if not isinstance(ev,list): errors.append("evidence_must_be_list"); ev=[]
    for i,x in enumerate(ev):
        if not isinstance(x,dict) or x.get("type") not in ALLOWED_EVIDENCE or not str(x.get("ref","")).strip():
            errors.append(f"invalid_evidence:{i}")
    if r.get("tier")=="A" and not ev: errors.append("tier_a_requires_evidence")
    if r.get("country") in {"Russia","Belarus"} and r.get("compliance_cleared") is not True:
        if r.get("transaction_ready") is True: errors.append("sensitive_market_transaction_not_cleared")
    return tuple(errors)
