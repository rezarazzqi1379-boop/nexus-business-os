import pytest

from nexus_control_plane.adaptive_org import build_mission_team, mission_team_is_minimal
from nexus_control_plane.workforce import Department
from nexus_control_plane.workforce_orchestrator import WorkflowKind


def test_procurement_team_assembles_only_required_workflow_capabilities():
    team = build_mission_team("mission:hydrotester", WorkflowKind.PROCUREMENT)
    assert mission_team_is_minimal(team)
    assert Department.INTELLIGENCE in team.departments
    assert Department.DEALS in team.departments
    assert Department.NEXUS_CORE in team.departments
    assert "nexus.engineering_reviewer" in team.capability_ids
    assert "marketing.content_engine" not in team.capability_ids


def test_marketing_team_does_not_pull_procurement_specialists():
    team = build_mission_team("mission:tailoring", WorkflowKind.MARKETING)
    assert mission_team_is_minimal(team)
    assert Department.MARKETING in team.departments
    assert "nexus.engineering_reviewer" not in team.capability_ids


def test_procurement_team_preserves_consequential_gate():
    team = build_mission_team("mission:kcl", WorkflowKind.PROCUREMENT)
    assert "nexus.approval_gateway" in team.consequential_capability_ids


def test_invalid_mission_id_fails_closed():
    with pytest.raises(ValueError, match="mission_id"):
        build_mission_team(" bad ", WorkflowKind.SALES)
