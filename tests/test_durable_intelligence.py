from durable_intelligence import *
def rec(i,p="CHAIN",state=EvidenceState.VERIFIED,src="S",origin="",vf="",vt=""):
 return DurableRecord(i,p,RecordKind.RELATION,"buyer","BUYS","chain",state,src,"2026-10-07",valid_from=vf,valid_to=vt,origin_id=origin)
def test_verified_requires_source(): assert not admissible(rec("1",src=""))
def test_cross_chat_recovery_is_project_isolated():
 assert [r.record_id for r in recover((rec("1"),rec("2","HYDRO")),"CHAIN")]==["1"]
def test_duplicate_origin_counts_once():
 assert independent_origins((rec("1",origin="O"),rec("2",origin="O")))==1
def test_same_web_origin_counts_once():
 assert independent_origins((rec("1",src="https://www.example.com/a"),rec("2",src="https://example.com/b")))==1
def test_invalid_temporal_range_rejected():
 assert not admissible(rec("1",vf="2026-10-08",vt="2026-10-07"))
def test_expired_record_not_current():
 assert current_verified((rec("1",vf="2026-01-01",vt="2026-09-30"),),"CHAIN","buyer","BUYS","2026-10-07")==()
def test_future_record_not_current():
 assert current_verified((rec("1",vf="2026-10-08"),),"CHAIN","buyer","BUYS","2026-10-07")==()
def test_supersession_removes_old_current_record():
 old=rec("old"); new=DurableRecord("new","CHAIN",RecordKind.RELATION,"buyer","BUYS","chain-v2",EvidenceState.VERIFIED,"S2","2026-10-08",supersedes="old")
 assert [r.record_id for r in current_verified((old,new),"CHAIN","buyer","BUYS","2026-10-08")]==["new"]
def test_capsule_does_not_promote_clue():
 c=cross_chat_capsule((rec("1"),rec("2",state=EvidenceState.CLUE,src="")),"CHAIN")
 assert c["verified"]==1 and c["clues"]==1
def test_checkpoint_requires_exact_green_head():
 good=CheckpointBinding("CHAIN","abc","abc","1280","SUCCESS","D1")
 bad=CheckpointBinding("CHAIN","abc","def","1280","SUCCESS","D1")
 assert checkpoint_valid(good) and not checkpoint_valid(bad)
 assert cross_chat_capsule((rec("1"),),"CHAIN",good)["checkpoint_bound"]
def test_wrong_project_checkpoint_not_bound():
 c=CheckpointBinding("HYDRO","abc","abc","1280","SUCCESS","D1")
 assert not cross_chat_capsule((rec("1"),),"CHAIN",c)["checkpoint_bound"]
