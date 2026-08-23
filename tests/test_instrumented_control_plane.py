from nexus_control_plane.control_plane import AgentSpec, Authority, ControlPlane, Goal, Maturity, WorkItem, WorkState
from nexus_control_plane.instrumented_control_plane import InstrumentedControlPlane


def _clock(values):
    iterator = iter(values)
    return lambda: next(iterator)


def _setup():
    cp = ControlPlane()
    cp.register_goal(Goal("g1", "Test Goal", "quality"))
    cp.register_agent(AgentSpec(
        id="a1",
        role="analyst",
        capabilities={"research"},
        authorities={Authority.READ, Authority.ANALYZE},
        maturity=Maturity.TESTED,
        project_scopes={"KCL"},
    ))
    return cp


def test_instrumented_control_plane_records_submit_route_complete_and_preserves_behavior():
    cp = _setup()
    observed = InstrumentedControlPlane(cp, clock_ms=_clock([0, 3, 10, 15, 20, 24]))
    item = WorkItem(
        id="w1",
        project_id="KCL",
        goal_id="g1",
        kind="research",
        required_capabilities={"research"},
        required_authorities={Authority.READ, Authority.ANALYZE},
    )

    observed.submit(item)
    assert cp.work["w1"].state is WorkState.CANDIDATE

    selected = observed.route("w1")
    assert selected == "a1"
    assert cp.work["w1"].state is WorkState.RUNNING

    observed.complete("w1", success=True, quality=0.9)
    assert cp.work["w1"].state is WorkState.DONE

    snapshot = observed.snapshot()
    assert snapshot.event_count == 3
    assert snapshot.accepted_decisions == 1
    assert snapshot.total_latency_ms == 12
    assert snapshot.successful_events == 3


def test_instrumented_control_plane_records_blocked_route_without_fabricating_decision():
    cp = _setup()
    observed = InstrumentedControlPlane(cp, clock_ms=_clock([0, 1, 2, 3]))
    item = WorkItem(
        id="w2",
        project_id="KCL",
        goal_id="g1",
        kind="research",
        required_capabilities={"missing-capability"},
        required_authorities={Authority.READ},
    )

    observed.submit(item)
    selected = observed.route("w2")
    assert selected is None
    assert cp.work["w2"].state is WorkState.BLOCKED

    route_event = observed.events[-1]
    assert route_event.accepted_decision is False
    assert route_event.success is False
    assert route_event.decision_ref is None


def test_human_correction_is_observed_as_override_not_hidden():
    cp = _setup()
    observed = InstrumentedControlPlane(cp, clock_ms=_clock([0, 1, 2, 3, 4, 5]))
    item = WorkItem(
        id="w3",
        project_id="KCL",
        goal_id="g1",
        kind="research",
        required_capabilities={"research"},
        required_authorities={Authority.READ},
    )

    observed.submit(item)
    observed.route("w3")
    observed.complete("w3", success=True, quality=0.7, human_correction=True)

    snapshot = observed.snapshot()
    assert snapshot.human_overrides == 1
    assert observed.events[-1].human_override is True
