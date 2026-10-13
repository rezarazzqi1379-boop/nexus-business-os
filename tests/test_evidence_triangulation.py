from evidence_triangulation import EvidenceRef,triangulate
def test_copied_sources_do_not_fake_independence():
 a=EvidenceRef("a","OFFICIAL_COMPANY","company-x");b=EvidenceRef("b","INDEPENDENT_SOURCE","company-x")
 assert triangulate([a,b])["independent_sources"]==1
 assert not triangulate([a,b])["verified"]
def test_independent_strong_evidence_can_verify():
 a=EvidenceRef("a","OFFICIAL_COMPANY","company-x");b=EvidenceRef("b","TRADE_DATASET","trade-y")
 assert triangulate([a,b])["verified"]
def test_contradiction_blocks_verification():
 a=EvidenceRef("a","OFFICIAL_COMPANY","company-x");b=EvidenceRef("b","TRADE_DATASET","trade-y");c=EvidenceRef("c","REGULATOR","reg-z",True,True)
 assert not triangulate([a,b,c])["verified"]
