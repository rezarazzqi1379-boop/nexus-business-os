"""Validation for evidence-native country lead records."""
from __future__ import annotations
from steel_evidence_quality import evidence_freshness
ALLOWED_ROLES={"END_USER","BUYER","IMPORTER","DISTRIBUTOR","COMPETITOR","STRATEGIC_PARTNER","UNKNOWN"}
ALLOWED_EVIDENCE={"OFFICIAL_COMPANY","OFFICIAL_CUSTOMS","TRADE_DATA","STANDARD","REGULATOR","INDEPENDENT","CLAIM"}
def validate_lead(r:dict,*,today=None)->tuple[str,...]:
    errors=[]
    for k in ("lead_id","country","company","role","applications","grade_candidates","evidence","status"):
        if k not in r:errors.append(f"missing:{k}")
    if r.get("role") not in ALLOWED_ROLES:errors.append("invalid_role")
    ev=r.get("evidence",[])
    if not isinstance(ev,list):errors.append("evidence_must_be_list");ev=[]
    valid_current=0
    qualifying_current=0
    for i,x in enumerate(ev):
        if not isinstance(x,dict) or x.get("type") not in ALLOWED_EVIDENCE or not str(x.get("ref","")).strip():
            errors.append(f"invalid_evidence:{i}");continue
        if not str(x.get("observed_at","")).strip():
            errors.append(f"evidence_date_required:{i}");continue
        fresh=evidence_freshness(x["observed_at"],today=today)
        if fresh in {"UNKNOWN","INVALID_FUTURE"}:errors.append(f"invalid_evidence_date:{i}")
        elif fresh=="STALE":errors.append(f"stale_evidence:{i}")
        else:
            valid_current+=1
            if x.get("type")!="CLAIM":qualifying_current+=1
    if r.get("tier")=="A" and valid_current==0:errors.append("tier_a_requires_current_evidence")
    if r.get("tier")=="A" and qualifying_current==0:errors.append("tier_a_requires_qualifying_evidence")
    if r.get("country") in {"Russia","Belarus"} and r.get("compliance_cleared") is not True and r.get("transaction_ready") is True:
        errors.append("sensitive_market_transaction_not_cleared")
    return tuple(errors)
