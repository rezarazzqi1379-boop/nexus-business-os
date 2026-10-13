from platform_runner_contract import RunnerPacket, admission_errors

def packet(**kw):
    d=dict(task_id="task-1", project_id="SANDBOX",
           canonical_source_refs=("registry:1",), expected_artifact="sandbox proof",
           evidence_requirements=("source locator",), tests=("pytest",),
           budget=100, allowed_actions=("read", "draft", "test"),
           prohibited_actions=("deploy", "send"), rollback="revert draft commit")
    d.update(kw)
    return RunnerPacket(**d)

def test_valid_packet_is_admitted():
    assert admission_errors(packet(), expected_project_id="SANDBOX") == ()

def test_cross_project_packet_is_blocked():
    assert "project_scope_mismatch" in admission_errors(packet(project_id="OTHER"), expected_project_id="SANDBOX")

def test_protected_deploy_is_blocked():
    assert "protected_action_not_permitted" in admission_errors(packet(allowed_actions=("read", "deploy")), expected_project_id="SANDBOX")

def test_missing_sources_is_blocked():
    assert "canonical_sources_missing" in admission_errors(packet(canonical_source_refs=()), expected_project_id="SANDBOX")

def test_budget_and_rollback_are_required():
    assert "budget_or_rollback_missing" in admission_errors(packet(budget=0, rollback=""), expected_project_id="SANDBOX")

def test_conflicting_permissions_are_blocked():
    assert "contradictory_permissions" in admission_errors(packet(allowed_actions=("read", "send"), prohibited_actions=("send",)), expected_project_id="SANDBOX")

def test_duplicate_source_refs_are_blocked():
    assert "duplicate_source_refs" in admission_errors(packet(canonical_source_refs=("registry:1", "registry:1")), expected_project_id="SANDBOX")
