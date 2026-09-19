import pytest

from conversation_control import ConversationSnapshot
from project_control_plane import WorkRequest, build_coordination_plan, build_portfolio_cycle
from source_failover import SourceHealth
from src.nexus_core.agent_catalog import AgentCatalogEntry


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


def agent(*, lifecycle="ADOPTED_ADAPTER", catalog_id="AGT-TEST"):
    return AgentCatalogEntry(
        catalog_id, "Test Agent", "AGENT", "https://example.invalid/agent",
        "2026-09-12", lifecycle, ("agent-runtime",), ("agents",),
        ("revisit",), "Pass the bounded test", "Remove the adapter",
    )


def test_builds_routed_scheduled_plan():
    plan = build_coordination_plan((request(),), (source(),), catalog=(agent(),))
    assert plan.assignments[0].work_id == "research-1"
    assert plan.source_routes["research-1"].selected == ("exa",)
    assert plan.schedule.running == ("research-1",)
    assert plan.blocked == ()


def test_external_work_is_never_auto_scheduled():
    plan = build_coordination_plan(
        (request(risk="external"),), (source(),), catalog=(agent(),)
    )
    assert plan.approval_required == ("research-1",)
    assert plan.schedule.running == ()
    assert plan.schedule.waiting == ("research-1",)


def test_unhealthy_or_write_source_blocks_research():
    plan = build_coordination_plan(
        (request(),), (source(read_only=False),), catalog=(agent(),)
    )
    assert ("research-1", "no_safe_read_source") in plan.blocked
    assert plan.schedule.running == ()


def test_duplicate_work_identity_fails_closed():
    with pytest.raises(ValueError, match="duplicate_work_id"):
        build_coordination_plan((request(), request()), (source(),))


def test_missing_agent_capability_blocks_work():
    plan = build_coordination_plan(
        (request(problem_tags=("not-real",), required_capabilities=("not-real",)),),
        (source(),),
        catalog=(agent(),),
    )
    assert ("research-1", "no_qualified_agent") in plan.blocked


@pytest.mark.parametrize("lifecycle", ("DISCOVERED", "WATCH", "DEFERRED"))
def test_observational_agent_lifecycles_never_execute(lifecycle):
    plan = build_coordination_plan(
        (request(),), (source(),), catalog=(agent(lifecycle=lifecycle),)
    )
    assert plan.assignments == ()
    assert plan.schedule.running == ()
    assert plan.schedule.waiting == ("research-1",)
    assert ("research-1", "no_qualified_agent") in plan.blocked


@pytest.mark.parametrize("lifecycle", ("EXPERIMENT", "SANDBOX_READY"))
def test_experimental_agents_are_sandbox_only(lifecycle):
    catalog = (agent(lifecycle=lifecycle),)
    normal = build_coordination_plan((request(),), (source(),), catalog=catalog)
    sandbox = build_coordination_plan(
        (request(lane="sandbox"),), (source(),), catalog=catalog
    )
    assert normal.schedule.running == ()
    assert sandbox.schedule.running == ("research-1",)
    assert sandbox.assignments[0].lifecycle == lifecycle


def test_sandbox_agent_cannot_execute_external_work():
    plan = build_coordination_plan(
        (request(lane="sandbox", risk="external"),),
        (source(),),
        catalog=(agent(lifecycle="EXPERIMENT"),),
    )
    assert plan.assignments == ()
    assert plan.approval_required == ("research-1",)
    assert plan.schedule.running == ()
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
    assert cycle.coordination.schedule.running == ()
    assert cycle.coordination.schedule.waiting
    assert cycle.token_allocation.output == 4_000
