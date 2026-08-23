from nexus_control_plane.control_plane import (
    Authority,
    ControlPlane,
    Goal,
    WorkItem,
    WorkState,
    requires_forge_preflight,
)
from nexus_control_plane.forge_preflight import ForgePreflightRequest


def _plane() -> ControlPlane:
    plane = ControlPlane()
    plane.register_goal(Goal(id="g1", name="Improve NEXUS", north_star_metric="safe_improvement"))
    return plane


def _item(kind: str, preflight=None) -> WorkItem:
    return WorkItem(
        id=f"w-{kind}",
        project_id="nexus",
        goal_id="g1",
        kind=kind,
        required_capabilities=set(),
        required_authorities={Authority.ANALYZE},
        forge_preflight=preflight,
    )


def _pf(**changes) -> ForgePreflightRequest:
    data = dict(
        change_id="chg-1",
        concern="forge_lifecycle",
        proposed_owner="PR36",
        evidence_refs=("github:PR36",),
        runtime_sensitive=False,
        live_verified=False,
        prior_failure_refs=(),
        prior_failures_consulted=False,
    )
    data.update(changes)
    return ForgePreflightRequest(**data)


def test_material_change_kinds_require_forge_but_normal_research_does_not():
    for kind in (
        "agent_change",
        "architecture_change",
        "business_engine_change",
        "connector_change",
        "evaluator_change",
        "learning_change",
        "project_mechanism_change",
        "workflow_change",
        "change:custom",
    ):
        assert requires_forge_preflight(kind) is True
    assert requires_forge_preflight("research") is False


def test_material_change_without_preflight_is_blocked_at_intake_and_not_routed():
    plane = _plane()
    item = _item("architecture_change")
    plane.submit(item)
    assert item.state is WorkState.BLOCKED
    assert "forge_preflight_required" in item.blockers
    assert plane.route(item.id) is None


def test_owner_conflict_blocks_before_agent_routing():
    plane = _plane()
    item = _item("evaluator_change", _pf(concern="evaluation", proposed_owner="PR99"))
    plane.submit(item)
    assert item.state is WorkState.BLOCKED
    assert any("canonical owner conflict" in blocker for blocker in item.blockers)
    assert plane.route(item.id) is None


def test_unknown_concern_is_review_hold_not_silently_routed():
    plane = _plane()
    item = _item("change:new_framework", _pf(concern="unknown_framework", proposed_owner="PR999"))
    plane.submit(item)
    assert item.state is WorkState.REVIEW
    assert any("no canonical owner" in blocker for blocker in item.blockers)
    assert plane.route(item.id) is None


def test_runtime_sensitive_unverified_change_is_review_hold():
    plane = _plane()
    item = _item("connector_change", _pf(runtime_sensitive=True, live_verified=False))
    plane.submit(item)
    assert item.state is WorkState.REVIEW
    assert any("not live-verified" in blocker for blocker in item.blockers)


def test_prior_failure_not_consulted_is_review_hold():
    plane = _plane()
    item = _item(
        "architecture_change",
        _pf(prior_failure_refs=("lesson:supabase-default-grant-drift",), prior_failures_consulted=False),
    )
    plane.submit(item)
    assert item.state is WorkState.REVIEW
    assert any("prior failures" in blocker for blocker in item.blockers)


def test_clean_registered_change_enters_ready_shadow_state_only():
    plane = _plane()
    item = _item("architecture_change", _pf())
    plane.submit(item)
    assert item.state is WorkState.READY
    assert item.assigned_agent is None


def test_existing_non_change_work_preserves_previous_intake_behavior():
    plane = _plane()
    item = _item("research")
    plane.submit(item)
    assert item.state is WorkState.CANDIDATE
    assert item.blockers == []
