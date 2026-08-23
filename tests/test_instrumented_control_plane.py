from nexus_control_plane.control_plane import AgentSpec, Authority, ControlPlane, Goal, Maturity, WorkItem, WorkState
from nexus_control_plane.instrumented_control_plane import InstrumentedControlPlane
from nexus_control_plane.telemetry_store import JsonlTelemetryStore


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


def _item(item_id="w1", capability="research"):
    return WorkItem(
        id=item_id,
        project_id="KCL",
        goal_id="g1",
        kind="research",
        required_capabilities={capability},
        required_authorities={Authority.READ},
    )


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
    item = _item("w2", capability="missing-capability")

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
    item = _item("w3")

    observed.submit(item)
    observed.route("w3")
    observed.complete("w3", success=True, quality=0.7, human_correction=True)

    snapshot = observed.snapshot()
    assert snapshot.human_overrides == 1
    assert observed.events[-1].human_override is True


def test_instrumented_control_plane_persists_events_to_durable_sink(tmp_path):
    cp = _setup()
    store = JsonlTelemetryStore(tmp_path / "runtime.jsonl")
    observed = InstrumentedControlPlane(cp, clock_ms=_clock([0, 1, 2, 3, 4, 5]), sink=store)
    item = _item("w4")

    observed.submit(item)
    observed.route("w4")
    observed.complete("w4", success=True, quality=0.9)

    persisted = store.read_all()
    assert len(persisted) == 3
    assert [event.event_id for event in persisted] == ["cp:1:submit", "cp:2:route", "cp:3:complete"]
    assert observed.telemetry_errors == []


def test_telemetry_sink_failure_does_not_undo_or_duplicate_business_action():
    class BrokenSink:
        def append(self, event):
            raise OSError("sink unavailable")

    cp = _setup()
    observed = InstrumentedControlPlane(cp, clock_ms=_clock([0, 1, 2, 3, 4, 5]), sink=BrokenSink())
    item = _item("w5")

    observed.submit(item)
    selected = observed.route("w5")
    observed.complete("w5", success=True, quality=0.9)

    assert selected == "a1"
    assert cp.work["w5"].state is WorkState.DONE
    assert len(cp.evaluations) == 1
    assert len(observed.events) == 3
    assert len(observed.telemetry_errors) == 3
