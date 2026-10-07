from durable_intelligence import *
def rec(i,p="CHAIN",state=EvidenceState.VERIFIED,src="S",origin=""):
 return DurableRecord(i,p,RecordKind.RELATION,"buyer","BUYS","chain",state,src,"2026-10-07",origin_id=origin)
def test_verified_requires_source(): assert not admissible(rec("1",src=""))
def test_cross_chat_recovery_is_project_isolated():
 assert [r.record_id for r in recover((rec("1"),rec("2","HYDRO")),"CHAIN")]==["1"]
def test_duplicate_origin_counts_once():
 assert independent_origins((rec("1",origin="O"),rec("2",origin="O")))==1
def test_supersession_removes_old_current_record():
 old=rec("old"); new=DurableRecord("new","CHAIN",RecordKind.RELATION,"buyer","BUYS","chain-v2",EvidenceState.VERIFIED,"S2","2026-10-08",supersedes="old")
 assert [r.record_id for r in current_verified((old,new),"CHAIN","buyer","BUYS")]==["new"]
def test_capsule_does_not_promote_clue():
 c=cross_chat_capsule((rec("1"),rec("2",state=EvidenceState.CLUE,src="")),"CHAIN")
 assert c["verified"]==1 and c["clues"]==1
