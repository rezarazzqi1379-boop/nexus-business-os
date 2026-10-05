"""Evidence-native Opportunity Graph primitives for NEXUS v3/v4."""
from dataclasses import dataclass
from steel_evidence_quality import evidence_freshness
from evidence_triangulation import EvidenceRef,triangulate
ALLOWED_STATES={"FACT","VERIFIED_EVIDENCE","CLAIM","ESTIMATE","ASSUMPTION","HYPOTHESIS","UNKNOWN","SUPERSEDED"}
@dataclass(frozen=True)
class GraphEdge:
    subject:str; predicate:str; object:str; state:str
    evidence_refs:tuple[str,...]=(); observed_at:str=""
def validate_edge(e:GraphEdge,*,today=None)->tuple[str,...]:
    errors=[]
    if not all(v.strip() for v in (e.subject,e.predicate,e.object)): errors.append("edge_terms_required")
    if e.state not in ALLOWED_STATES: errors.append("invalid_state")
    verified=e.state in {"FACT","VERIFIED_EVIDENCE"}
    if verified and not e.evidence_refs: errors.append("verified_edge_requires_evidence")
    if e.evidence_refs and any(not r.strip() for r in e.evidence_refs): errors.append("invalid_evidence_ref")
    if e.evidence_refs and not e.observed_at.strip(): errors.append("evidence_date_required")
    if verified and e.observed_at and evidence_freshness(e.observed_at,today=today)!="FRESH": errors.append("verified_edge_requires_fresh_evidence")
    return tuple(errors)
def can_promote_verified(edge:GraphEdge,evidence:tuple[EvidenceRef,...],*,today=None)->bool:
    """High-value promotion requires structural validity plus independent, current, non-contradicted evidence."""
    candidate=GraphEdge(edge.subject,edge.predicate,edge.object,"VERIFIED_EVIDENCE",edge.evidence_refs,edge.observed_at)
    if validate_edge(candidate,today=today): return False
    refs={x.ref for x in evidence}
    if not set(edge.evidence_refs).issubset(refs): return False
    return bool(triangulate(evidence)["verified"])
