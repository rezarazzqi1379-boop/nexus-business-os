from nexus_control_plane.control_plane import ControlPlane, Goal, WorkItem, WorkState
from nexus_control_plane.next_best_action import ActionCandidate
from nexus_control_plane.portfolio_selector import select_next_ready_work


def candidate(action_id, project_id="P", **overrides):
    data = dict(
        action_id=action_id,
        project_id=project_id,
        action_type="research",
        evidence_readiness=0.8,
        expected_value=0.7,
        information_gain=0.7,
        urgency=0.5,
        reversibility=0.9,
        risk=0.2,
        cost=0.2,
        dependency_ready=True,
        source_authority_ok=True,
        unresolved_contradictions=0,
        prior_failures_consulted=True,
    )
    data.update(overrides)
    return ActionCandidate(**data)


def setup_plane():
    cp = ControlPlane()
    cp.register_goal(Goal("g", "goal", "metric"))
    return cp


def add_work(cp, work_id, state, project_id="P"):
    item = WorkItem(work_id, project_id, "g", "analysis", set(), set(), state=state)
    cp.work[work_id] = item
    return item


def test_selector_ignores_higher_score_blocked_work_state():
    cp = setup_plane()
    add_work(cp, "blocked", WorkState.BLOCKED)
    add_work(cp, "ready", WorkState.READY)
    result = select_next_ready_work(
        cp,
        (
            candidate("blocked", expected_value=1.0, information_gain=1.0),
            candidate("ready", expected_value=0.4, information_gain=0.4),
        ),
    )
    assert result.selected_work_id == "ready"
    assert any("not ready" in reason for reason in result.reasons)


def test_selector_never_selects_review_item():
    cp = setup_plane()
    add_work(cp, "review", WorkState.REVIEW)
    result = select_next_ready_work(cp, (candidate("review", expected_value=1.0),))
    assert result.selected_work_id is None


def test_selector_respects_nba_block_even_when_work_is_ready():
    cp = setup_plane()
    add_work(cp, "x", WorkState.READY)
    result = select_next_ready_work(cp, (candidate("x", source_authority_ok=False),))
    assert result.selected_work_id is None
    assert any("NBA blocked" in reason for reason in result.reasons)


def test_selector_blocks_project_mismatch():
    cp = setup_plane()
    add_work(cp, "x", WorkState.READY, project_id="A")
    result = select_next_ready_work(cp, (candidate("x", project_id="B"),))
    assert result.selected_work_id is None
    assert any("project mismatch" in reason for reason in result.reasons)


def test_selector_is_advisory_and_does_not_route_or_mutate_ready_state():
    cp = setup_plane()
    item = add_work(cp, "x", WorkState.READY)
    result = select_next_ready_work(cp, (candidate("x"),))
    assert result.selected_work_id == "x"
    assert item.state is WorkState.READY
    assert item.assigned_agent is None
