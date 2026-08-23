import pytest

from nexus_control_plane.workflow_audit import (
    ImprovementAction,
    WorkflowObservation,
    audit_workflow,
)


def obs(project, *, rework=0, duplicate=0, late=False, evidence=True, touches=3, duration=20, outcome=True):
    return WorkflowObservation(
        workflow_id="procurement.rfq",
        project_id=project,
        duration_minutes=duration,
        manual_touch_count=touches,
        rework_count=rework,
        duplicate_count=duplicate,
        blocker_discovered_after_outreach=late,
        evidence_complete=evidence,
        outcome_observed=outcome,
    )


def test_late_blocker_pattern_prefers_pre_action_gate():
    result = audit_workflow((
        obs("hydro", late=True, rework=1),
        obs("can", late=True, rework=1),
        obs("kcl", late=False),
    ))
    assert result.recommendation is ImprovementAction.ADD_GATE
    assert result.late_blocker_rate == pytest.approx(2 / 3)


def test_missing_measurements_are_not_treated_as_zero():
    item = WorkflowObservation(
        workflow_id="procurement.rfq",
        project_id="open-case",
        duration_minutes=None,
        manual_touch_count=None,
        rework_count=None,
        duplicate_count=None,
        blocker_discovered_after_outreach=None,
        evidence_complete=None,
        outcome_observed=False,
    )
    result = audit_workflow((item,))
    assert result.mean_duration_minutes is None
    assert result.rework_rate is None
    assert result.duplicate_rate is None
    assert result.recommendation is ImprovementAction.KEEP


def test_stable_cross_project_manual_work_can_be_automation_candidate():
    result = audit_workflow((
        obs("p1", touches=5),
        obs("p2", touches=4),
        obs("p3", touches=6),
        obs("p4", touches=4),
        obs("p5", touches=5),
    ))
    assert result.recommendation is ImprovementAction.AUTOMATE


def test_evidence_gaps_prevent_automation_recommendation():
    result = audit_workflow((
        obs("p1", evidence=False, touches=5),
        obs("p2", evidence=False, touches=5),
        obs("p3", evidence=True, touches=5),
        obs("p4", evidence=False, touches=5),
        obs("p5", evidence=True, touches=5),
    ))
    assert result.recommendation is ImprovementAction.RESEARCH


def test_mixed_workflow_ids_fail_closed():
    a = obs("p1")
    b = WorkflowObservation(
        workflow_id="sales.outbound",
        project_id="p2",
        duration_minutes=10,
        manual_touch_count=2,
        rework_count=0,
        duplicate_count=0,
        blocker_discovered_after_outreach=False,
        evidence_complete=True,
        outcome_observed=True,
    )
    with pytest.raises(ValueError, match="single workflow_id"):
        audit_workflow((a, b))


def test_negative_measurements_fail_closed():
    bad = obs("p1", duration=-1)
    with pytest.raises(ValueError, match="non-negative"):
        audit_workflow((bad,))
