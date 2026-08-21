import pytest

from nexus_autonomy.signal_router import ProjectSignal, route_signals, signal_to_work_item


def _signal(**overrides):
    data = dict(
        signal_id="kcl:reply:1",
        project_id="kcl-import",
        kind="supplier_reply",
        summary="supplier returned a new commercial response requiring verification",
        evidence_refs=("gmail:message:1",),
        value="high",
        urgency="high",
        evidence="partial",
        cost="low",
    )
    data.update(overrides)
    return ProjectSignal(**data)


def test_signal_routes_to_research_only_work():
    work = signal_to_work_item(_signal())
    assert work.domain == "research"
    assert work.action_kind == "research"
    assert work.write_required is False
    assert work.reversible is True
    assert work.goal_ref == "project:kcl-import"


def test_router_prioritizes_value_then_urgency_then_evidence_then_cost():
    low = _signal(signal_id="a", project_id="can-line", value="medium")
    high = _signal(signal_id="b", project_id="hydrotest", value="high", urgency="critical")
    critical = _signal(signal_id="c", project_id="kcl", value="critical", urgency="low")
    routed = route_signals((low, high, critical))
    assert [item.signal.signal_id for item in routed] == ["c", "b", "a"]


def test_duplicate_signal_ids_are_deduplicated():
    first = _signal(signal_id="same")
    second = _signal(signal_id="same", project_id="other")
    routed = route_signals((first, second))
    assert len(routed) == 1
    assert routed[0].signal.project_id == "kcl-import"


def test_missing_evidence_fails_closed():
    with pytest.raises(ValueError, match="evidence_refs"):
        signal_to_work_item(_signal(evidence_refs=()))


def test_invalid_priority_fails_closed():
    with pytest.raises(ValueError, match="priority"):
        signal_to_work_item(_signal(value="urgent"))


def test_project_boundaries_are_preserved_in_task_and_goal():
    work = signal_to_work_item(_signal(signal_id="hydro:1", project_id="hydrotest"))
    assert work.task_id == "signal:hydro:1"
    assert work.goal_ref == "project:hydrotest"
    assert "hydrotest" in work.objective


def test_router_is_deterministic_for_equal_scores():
    b = _signal(signal_id="2", project_id="z-project")
    a = _signal(signal_id="1", project_id="a-project")
    routed = route_signals((b, a))
    assert [item.signal.project_id for item in routed] == ["a-project", "z-project"]
