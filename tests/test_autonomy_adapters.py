from nexus_core.autonomy import WorkItem, plan_autonomy, validate_work_item
from nexus_core.autonomy_adapters import (
    backup_due_work_item, ci_failure_work_item, cross_ai_review_work_item,
    customer_network_research_work_item, inbox_reply_work_item,
    learning_signal_work_item, news_signal_work_item, plugin_candidate_work_item,
    plugin_connect_work_item, research_signal_work_item,
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
        cross_ai_review_work_item(source_ref="notion:claude-review:1", review_key="pr13", code_change_relevant=True),
        customer_network_research_work_item(source_ref="market:iran-industrial-buyers", market_key="industrial-buyers", commercially_relevant=True),
        learning_signal_work_item(source_ref="docs:primary-agent-runtime", topic_key="agent-runtime", implementation_relevant=True),
        news_signal_work_item(source_ref="news:shipping-route", topic_key="shipping-route", business_impact=True),
        backup_due_work_item(source_ref="notion:command-center", scope_key="command-center"),
        plugin_candidate_work_item(source_ref="plugin:catalog:example", plugin_key="security-tool"),
    )
    plan = plan_autonomy(tasks, capabilities())
    runnable_ids = {item.task.task_id for item in plan.runnable}
    assert {"reply-review:hydrotester-yaxing", "ci-failure:autonomy-fabric", "research:agent-evals", "cross-ai-review:pr13", "customer-network:industrial-buyers", "learning:agent-runtime", "news:shipping-route", "backup:command-center", "plugin-review:security-tool"} <= runnable_ids
    assert plan.human_gated == ()


def test_code_blind_cross_ai_review_is_explicitly_unverified():
    task = cross_ai_review_work_item(source_ref="notion:claude-review:1", review_key="security-review", code_change_relevant=True)
    assert task.action_kind == "research" and task.write_required is False
    assert task.evidence == "unverified" and task.acceptable_capability_ids == ("github.read",)
    assert "not authorization" in task.objective


def test_cross_ai_review_requires_retrievable_code_proof_for_partial_evidence():
    task = cross_ai_review_work_item(
        source_ref="notion:claude-review:1",
        review_key="security-review",
        code_change_relevant=True,
        code_review_proof_ref="github:commit:abc123",
    )
    assert task.evidence == "partial"
    assert task.evidence_refs == ("notion:claude-review:1", "github:commit:abc123")
    assert task.action_kind == "research" and task.write_required is False


def test_arbitrary_claim_of_code_review_does_not_upgrade_evidence():
    task = cross_ai_review_work_item(
        source_ref="notion:claude-review:1",
        review_key="security-review",
        code_change_relevant=True,
        code_review_proof_ref="reviewer-says-i-read-it",
    )
    assert task.evidence == "unverified"
    assert task.evidence_refs == ("notion:claude-review:1",)


def test_cross_ai_review_cannot_request_write_or_send_capability():
    task = cross_ai_review_work_item(
        source_ref="notion:claude-review:1",
        review_key="boundary",
        code_change_relevant=True,
        code_review_proof_ref="sha256:123456",
    )
    assert task.acceptable_capability_ids == ("github.read",) and task.action_kind == "research" and task.write_required is False


def test_customer_network_research_is_outcome_bound_but_never_outreach_authorized():
    task = customer_network_research_work_item(source_ref="market:buyer-map", market_key="buyer-map", commercially_relevant=True)
    assert task.action_kind == "research" and task.write_required is False and task.domain == "customer_network"
    assert task.goal_ref == "goal:customer-network:buyer-map"
    assert "verified company fit" in task.success_signal
    assert "credible buying/project/need evidence" in task.success_signal
    assert "direct or warm contact path" in task.success_signal
    assert "invitation counts" in task.failure_signal
    assert "kill, narrow or change the segment" in task.failure_signal
    assert "human-reviewed outreach only" in task.objective


def test_inbox_reply_is_bound_to_blocker_resolution_not_activity():
    task = inbox_reply_work_item(message_ref="gmail:message:abc", thread_key="supplier-thread", decision_relevant=True, external_reply_needed=True)
    assert task.action_kind == "draft" and task.write_required is False
    assert task.goal_ref == "goal:commercial-thread:supplier-thread"
    assert "blocker is resolved" in task.success_signal
    assert "required engineering/commercial evidence is still missing" in task.failure_signal


def test_learning_adapter_requires_testable_result_or_explicit_no_action():
    task = learning_signal_work_item(source_ref="docs:primary", topic_key="agent-runtime", implementation_relevant=True)
    assert task.goal_ref == "goal:technical-learning:agent-runtime"
    assert "testable implementation" in task.success_signal
    assert "passive summary" in task.failure_signal


def test_partial_outcome_contract_fails_closed():
    task = WorkItem(
        "bad-outcome", "research", "Research safely.", "research", ("web.search",), ("source:test",),
        goal_ref="goal:test",
    )
    errors = validate_work_item(task)
    assert "outcome contract requires goal_ref, success_signal and failure_signal together" in errors


def test_plugin_review_and_plugin_connection_are_separate_gates():
    plan = plan_autonomy((plugin_candidate_work_item(source_ref="plugin:catalog:example", plugin_key="security-tool"), plugin_connect_work_item(source_ref="review:security-tool:approved-candidate", plugin_key="security-tool")), capabilities())
    assert [i.task.task_id for i in plan.runnable] == ["plugin-review:security-tool"]
    assert [i.task.task_id for i in plan.human_gated] == ["plugin-connect:security-tool"]
