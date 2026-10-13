from evidence_quality import *

def q(eid="e1",project="P1",root="official.example",authority=AuthorityLevel.PRIMARY,freshness=EvidenceFreshness.CURRENT,direct=True,contradicted=False):
 return QualityEvidence(eid,project,root,authority,freshness,direct,contradicted)

def test_primary_current_direct_has_full_weight():
 assert evidence_weight(q())==1.0

def test_same_origin_copies_do_not_inflate():
 assert independent_quality((q("a"),q("b")), "P1")==1.0

def test_independent_primary_origins_accumulate_transparently():
 assert independent_quality((q("a"),q("b",root="other.example")), "P1")==2.0
 assert quality_band(2.0)=="STRONG_MULTI_ORIGIN"

def test_discovery_and_stale_evidence_are_downweighted():
 assert evidence_weight(q(authority=AuthorityLevel.DISCOVERY))<evidence_weight(q())
 assert evidence_weight(q(freshness=EvidenceFreshness.STALE))<evidence_weight(q())

def test_contradicted_evidence_contributes_zero():
 assert evidence_weight(q(contradicted=True))==0.0

def test_cross_project_evidence_does_not_inflate():
 assert independent_quality((q("a"),q("b",project="P2",root="other.example")),"P1")==1.0

def test_score_never_authorizes_action():
 assert not may_authorize_action(999.0)
