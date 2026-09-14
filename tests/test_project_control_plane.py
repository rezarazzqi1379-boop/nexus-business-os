import pytest

from conversation_control import ConversationSnapshot
from project_control_plane import WorkRequest, build_coordination_plan, build_portfolio_cycle
from source_failover import SourceHealth


def request(**changes):
    values = dict(
        work_id="research-1", project_id="PRJ-1", objective="Map viable agent runtimes",
        problem_tags=("agent-runtime",), required_capabilities=("agents",),
    )
    values.update(changes)
    return WorkRequest(**values)


def source(**changes):
    values = dict(source_id="exa", available=True, read_only=True, auth_error=False,
                  cost_per_query=0.0, evidence_ref="probe:exa:ok")
    values.update(changes)
    return SourceHealth(**values)


def test_builds_routed_scheduled_plan():
    plan = build_coordination_plan((request(),), (source(),))
    assert plan.assignments[0].work_id == "research-1"
    assert plan.source_routes["research-1"].selected == ("exa",)
    assert plan.schedule.running == ("research-1",)
    assert plan.blocked == ()


def test_external_work_is_never_auto_scheduled():
    plan = build_coordination_plan((request(risk="external"),), (source(),))
    assert plan.approval_required == ("research-1",)
    assert plan.schedule.running == ()
    assert plan.schedule.waiting == ("research-1",)


def test_unhealthy_or_write_source_blocks_research():
    plan = build_coordination_plan((request(),), (source(read_only=False),))
    assert ("research-1", "no_safe_read_source") in plan.blocked
    assert plan.schedule.running == ()


def test_duplicate_work_identity_fails_closed():
    with pytest.raises(ValueError, match="duplicate_work_id"):
        build_coordination_plan((request(), request()), (source(),))


def test_missing_agent_capability_blocks_work():
    plan = build_coordination_plan(
        (request(problem_tags=("not-real",), required_capabilities=("not-real",)),),
        (source(),),
    )
    assert ("research-1", "no_qualified_agent") in plan.blocked


def test_portfolio_cycle_turns_conversation_need_into_scheduled_idea():
    snapshot = ConversationSnapshot(
        "thread-1", "Supplier research", "", "PRJ-KCL-01", "idle", 100, "thread:thread-1"
    )
    cycle = build_portfolio_cycle(
        (snapshot,), (source(),), now=100,
        estimated_history_tokens=50_000, estimated_evidence_tokens=10_000,
    )
    assert cycle.needs and cycle.ideas
    assert cycle.coordination.schedule.running
    assert cycle.token_allocation.output == 4_000
