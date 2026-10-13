from management_program import *
def m(i="M",**kw):
 d=dict(mission_id=i,project_id="CHAIN",objective="verified conversion",bottleneck="buyer relation",acceptance_test="one verified path",metric_name="verified_paths",baseline=0,target=1,owner_role="commercial intelligence",evidence_refs=("E1",),next_safe_action="verify buyer")
 d.update(kw);return Mission(**d)
def test_active_requires_evidence():assert not admit_active(m(evidence_refs=()))
def test_unknown_routes_verify():assert mission_state(m(critical_unknowns=("winner",)))==MissionState.VERIFY
def test_contradiction_blocks():assert mission_state(m(contradiction=True))==MissionState.BLOCKED
def test_protected_action_gated():assert mission_state(m(protected_action=True))==MissionState.GATED
def test_wip_limit():assert len(portfolio((m("1"),m("2"),m("3"),m("4")),3))==3
def test_duplicate_mission_rejected():
 try:portfolio((m("1"),m("1")));assert False
 except ValueError:pass
def test_close_requires_measurement_and_green():assert may_close(m(),1,True) and not may_close(m(),1,False)
def test_activity_without_metric_contract_not_active():assert not admit_active(m(metric_name=""))
