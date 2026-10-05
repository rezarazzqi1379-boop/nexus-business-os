from chain_evidence_binding import *
from evidence_triangulation import EvidenceRef

def test_two_independent_company_facts_do_not_verify_relationship():
 bs=(BoundEdgeEvidence("MetPromKo|STOCKED|40HN2MA",EvidenceRef("m","OFFICIAL_COMPANY","metpromko")),
     BoundEdgeEvidence("Gidrolast|USED|42CrMo4",EvidenceRef("g","OFFICIAL_COMPANY","gidrolast")))
 assert not can_verify_bound_edge(edge_key="MetPromKo|SUPPLIED_TO|Gidrolast",bindings=bs)

def test_relationship_requires_evidence_bound_to_same_edge():
 bs=(BoundEdgeEvidence("A|SUPPLIED_TO|B",EvidenceRef("a","OFFICIAL_COMPANY","a")),
     BoundEdgeEvidence("A|SUPPLIED_TO|B",EvidenceRef("b","OFFICIAL_CUSTOMS","customs")))
 assert can_verify_bound_edge(edge_key="A|SUPPLIED_TO|B",bindings=bs)
