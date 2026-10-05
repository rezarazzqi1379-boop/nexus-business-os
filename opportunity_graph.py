"""Evidence-native Opportunity Graph primitives for NEXUS v3."""
from dataclasses import dataclass
ALLOWED_STATES={"FACT","VERIFIED_EVIDENCE","CLAIM","ESTIMATE","ASSUMPTION","HYPOTHESIS","UNKNOWN","SUPERSEDED"}
@dataclass(frozen=True)
class GraphEdge:
    subject:str; predicate:str; object:str; state:str
    evidence_refs:tuple[str,...]=(); observed_at:str=""
def validate_edge(e:GraphEdge)->tuple[str,...]:
    errors=[]
    if not all(v.strip() for v in (e.subject,e.predicate,e.object)): errors.append("edge_terms_required")
    if e.state not in ALLOWED_STATES: errors.append("invalid_state")
    if e.state in {"FACT","VERIFIED_EVIDENCE"} and not e.evidence_refs: errors.append("verified_edge_requires_evidence")
    if e.evidence_refs and not e.observed_at.strip(): errors.append("evidence_date_required")
    return tuple(errors)
