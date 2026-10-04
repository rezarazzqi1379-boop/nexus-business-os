import pytest

from nexus_control_plane.project_fabric import (
    ProjectDomain,
    ProjectProfile,
    ProjectState,
    coordinate_portfolio,
)


def project(project_id, *, domain=ProjectDomain.PROCUREMENT, state=ProjectState.ACTIVE,
            value=80, urgency=70, evidence=.8, risk=30, attention=30,
            authority=True, outcome=False):
    return ProjectProfile(
        project_id=project_id,
        domain=domain,
        state=state,
        strategic_value=value,
        urgency=urgency,
        evidence_quality=evidence,
        downside_risk=risk,
        human_attention_cost=attention,
        has_authoritative_requirements=authority,
        has_measured_outcome=outcome,
    )


def test_waiting_projects_do_not_generate_duplicate_execution():
    result = coordinate_portfolio((project("can-forming", state=ProjectState.WAITING),))
    assert result[0].action == "watch_no_duplicate_action"


def test_engineering_project_without_authority_is_authority_first():
    result = coordinate_portfolio((project("hydro", domain=ProjectDomain.ENGINEERING, authority=False),))
    assert result[0].action == "authority_first"


def test_low_evidence_project_researches_before_execution():
    result = coordinate_portfolio((project("new-market", domain=ProjectDomain.RESEARCH, evidence=.2),))
    assert result[0].action == "research_first"


def test_measured_project_moves_to_optimization():
    result = coordinate_portfolio((project("kcl", outcome=True),))
    assert result[0].action == "optimize"


def test_priority_orders_value_without_ignoring_risk_and_attention():
    high = project("high", value=95, urgency=90, evidence=.9, risk=20, attention=20)
    noisy = project("noisy", value=95, urgency=90, evidence=.9, risk=90, attention=95)
    result = coordinate_portfolio((noisy, high))
    assert result[0].project_id == "high"


def test_duplicate_project_ids_fail_closed():
    with pytest.raises(ValueError, match="duplicate project_id"):
        coordinate_portfolio((project("same"), project("same")))
