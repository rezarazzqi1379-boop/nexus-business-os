from datetime import date
from commercial_chain_graph import candidate_edge
from commercial_chain_adapter import bind_and_promote
from evidence_triangulation import EvidenceRef

def test_chain_uses_existing_opportunity_evidence_gate():
 e=candidate_edge(source_id="mill",relation="SUPPLIED_TO",target_id="buyer",evidence_refs=("a","b"),observed_at="2026-10-05")
 one=(EvidenceRef("a","OFFICIAL_COMPANY","official"),EvidenceRef("b","INDEPENDENT_SOURCE","official"))
 assert bind_and_promote(e,one,today=date(2026,10,5)).state=="CANDIDATE"
 two=(EvidenceRef("a","OFFICIAL_COMPANY","official"),EvidenceRef("b","INDEPENDENT_SOURCE","independent"))
 assert bind_and_promote(e,two,today=date(2026,10,5)).state=="VERIFIED"

def test_contradiction_blocks_chain_promotion():
 e=candidate_edge(source_id="mill",relation="SUPPLIED_TO",target_id="buyer",evidence_refs=("a","b"),observed_at="2026-10-05")
 ev=(EvidenceRef("a","OFFICIAL_COMPANY","official"),EvidenceRef("b","INDEPENDENT_SOURCE","independent",contradicts=True))
 assert bind_and_promote(e,ev,today=date(2026,10,5)).state=="CANDIDATE"
