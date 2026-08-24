from pathlib import Path

from nexus_brain.runtime_snapshot import live_command_projection, load_manual_snapshot


SNAPSHOT = Path("data/operational/live_evidence_snapshot_2026-08-24.json")


def by_project(portfolio):
    return {item["project_id"]: item for item in portfolio["projects"]}


def test_manual_snapshot_loader_preserves_read_only_semantics():
    signals = load_manual_snapshot(SNAPSHOT)
    assert signals
    assert all(signal.source_ref.startswith("gmail:") for signal in signals)


def test_live_command_projection_surfaces_current_evidence_and_internal_actions():
    portfolio = live_command_projection(SNAPSHOT)
    projects = by_project(portfolio)
    assert portfolio["external_execution_allowed"] is False
    assert portfolio["action_required_count"] == 2
    assert projects["PRJ-KCL-01"]["counts"]["live_communications"] >= 2
    assert projects["PRJ-HYD-01"]["counts"]["recommended_internal_actions"] == 1
    assert projects["PRJ-KCL-01"]["counts"]["recommended_internal_actions"] == 1


def test_live_projection_does_not_bypass_project_blockers():
    projects = by_project(live_command_projection(SNAPSHOT))
    assert projects["PRJ-KCL-01"]["consequential_use_allowed"] is False
    assert projects["PRJ-HYD-01"]["consequential_use_allowed"] is False
    assert "blocking_unknown" in projects["PRJ-KCL-01"]["blockers"]
    assert "blocking_unknown" in projects["PRJ-HYD-01"]["blockers"]


def test_action_queue_is_exactly_scoped_to_source_evidence():
    projects = by_project(live_command_projection(SNAPSHOT))
    kcl = projects["PRJ-KCL-01"]["recommended_internal_actions"][0]
    hyd = projects["PRJ-HYD-01"]["recommended_internal_actions"][0]
    assert kcl["source_node_id"] == "LIVE-KCL-OMS-PERMIT-20260824"
    assert hyd["source_node_id"] == "LIVE-HYD-GH-REV12-ACK-20260823"
    assert kcl["external_execution_allowed"] is False
    assert hyd["external_execution_allowed"] is False
