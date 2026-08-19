from nexus_core.autonomy import plan_autonomy
from nexus_core.autonomy_adapters import (
    backup_due_work_item,
    ci_failure_work_item,
    cross_ai_review_work_item,
    customer_network_research_work_item,
    inbox_reply_work_item,
    learning_signal_work_item,
    news_signal_work_item,
    plugin_candidate_work_item,
    plugin_connect_work_item,
    research_signal_work_item,
)
from nexus_core.capabilities import Capability


def capabilities():
    return (
        Capability("gmail.read", "Read Gmail", ("gmail",), True, False, "available", proof_ref="connector:gmail"),
        Capability("notion.write", "Write Notion", ("notion",), True, True, "available", proof_ref="connector:notion"),
        Capability("github.write", "Write GitHub branch", ("github",), True, True, "available", proof_ref="connector:github"),
        Capability("github.read", "Read GitHub code", ("github",), True, False, "available", proof_ref="connector:github"),
        Capability("web.search", "Search authoritative web sources", ("web",), True, False, "available", proof_ref="tool:web"),
        Capability("exa.search", "Search research sources", ("exa",), True, False, "degraded", proof_ref="connector:exa"),
        Capability("linkedin.read", "Read professional profiles", ("linkedin",), True, False, "available", proof_ref="connector:linkedin"),
        Capability("drive.write", "Write Drive backup", ("drive",), True, True, "blocked", proof_ref=""),
        Capability("plugin.catalog", "Read plugin catalog", ("plugins",), True, False, "available", proof_ref="connector:plugin-management"),
        Capability("plugin.manage", "Change plugin access", ("plugins",), True, True, "available", approval_mode="human_before_external_write", proof_ref="connector:plugin-management"),
    )


def test_real_source_adapters_route_safe_work_without_external_side_effects():
    tasks = (
        inbox_reply_work_item(message_ref="gmail:message:abc", thread_key="hydrotester-yaxing", decision_relevant=True, external_reply_needed=True),
        ci_failure_work_item(run_ref="github:actions:123", branch_key="autonomy-fabric"),
        research_signal_work_item(source_ref="paper:example", topic_key="agent-evals", decision_relevant=True),
        cross_ai_review_work_item(source_ref="drive:claude-bridge:revision-1", review_key="pr13", code_change_relevant=True),
        customer_network_research_work_item(source_ref="market:iran-industrial-buyers", market_key="industrial-buyers", commercially_relevant=True),
        learning_signal_work_item(source_ref="docs:primary-agent-runtime", topic_key="agent-runtime", implementation_relevant=True),
        news_signal_work_item(source_ref="news:shipping-route", topic_key="shipping-route", business_impact=True),
        backup_due_work_item(source_ref="notion:command-center", scope_key="command-center"),
        plugin_candidate_work_item(source_ref="plugin:catalog:example", plugin_key="security-tool"),
    )
    plan = plan_autonomy(tasks, capabilities())
    runnable_ids = {item.task.task_id for item in plan.runnable}
    assert "reply-review:hydrotester-yaxing" in runnable_ids
    assert "ci-failure:autonomy-fabric" in runnable_ids
    assert "research:agent-evals" in runnable_ids
    assert "cross-ai-review:pr13" in runnable_ids
    assert "customer-network:industrial-buyers" in runnable_ids
    assert "learning:agent-runtime" in runnable_ids
    assert "news:shipping-route" in runnable_ids
    assert "backup:command-center" in runnable_ids
    assert "plugin-review:security-tool" in runnable_ids
    assert plan.human_gated == ()


def test_cross_ai_review_is_untrusted_research_not_authorization():
    task = cross_ai_review_work_item(
        source_ref="drive:claude-bridge:revision-1",
        review_key="security-review",
        code_change_relevant=True,
    )
    assert task.action_kind == "research"
    assert task.write_required is False
    assert task.evidence == "partial"
    assert task.acceptable_capability_ids == ("github.read",)
    assert "not authorization" in task.objective


def test_customer_network_research_never_implies_outreach_authorization():
    task = customer_network_research_work_item(
        source_ref="market:buyer-map",
        market_key="buyer-map",
        commercially_relevant=True,
    )
    assert task.action_kind == "research"
    assert task.write_required is False
    assert task.domain == "customer_network"


def test_learning_adapter_demands_implementation_relevance_before_high_urgency():
    high = learning_signal_work_item(
        source_ref="docs:primary",
        topic_key="high",
        implementation_relevant=True,
    )
    low = learning_signal_work_item(
        source_ref="docs:background",
        topic_key="low",
        implementation_relevant=False,
    )
    assert high.value == "high"
    assert high.urgency == "medium"
    assert low.urgency == "low"


def test_news_adapter_stays_research_only_even_when_business_impact_is_high():
    task = news_signal_work_item(
        source_ref="news:critical",
        topic_key="critical",
        business_impact=True,
    )
    assert task.action_kind == "research"
    assert task.urgency == "high"


def test_plugin_review_and_plugin_connection_are_separate_gates():
    plan = plan_autonomy(
        (
            plugin_candidate_work_item(source_ref="plugin:catalog:example", plugin_key="security-tool"),
            plugin_connect_work_item(source_ref="review:security-tool:approved-candidate", plugin_key="security-tool"),
        ),
        capabilities(),
    )
    assert [item.task.task_id for item in plan.runnable] == ["plugin-review:security-tool"]
    assert [item.task.task_id for item in plan.human_gated] == ["plugin-connect:security-tool"]


def test_inbox_adapter_never_turns_reply_needed_into_auto_send():
    task = inbox_reply_work_item(
        message_ref="gmail:message:abc",
        thread_key="supplier-thread",
        decision_relevant=True,
        external_reply_needed=True,
    )
    assert task.action_kind == "draft"
    assert task.write_required is False
