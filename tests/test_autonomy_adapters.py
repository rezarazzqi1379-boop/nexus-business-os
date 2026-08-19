from nexus_core.autonomy import plan_autonomy
from nexus_core.autonomy_adapters import (
    backup_due_work_item,
    ci_failure_work_item,
    inbox_reply_work_item,
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
        Capability("web.search", "Search authoritative web sources", ("web",), True, False, "available", proof_ref="tool:web"),
        Capability("exa.search", "Search research sources", ("exa",), True, False, "degraded", proof_ref="connector:exa"),
        Capability("drive.write", "Write Drive backup", ("drive",), True, True, "blocked", proof_ref=""),
        Capability("plugin.catalog", "Read plugin catalog", ("plugins",), True, False, "available", proof_ref="connector:plugin-management"),
        Capability("plugin.manage", "Change plugin access", ("plugins",), True, True, "available", approval_mode="human_before_external_write", proof_ref="connector:plugin-management"),
    )


def test_real_source_adapters_route_safe_work_without_external_side_effects():
    tasks = (
        inbox_reply_work_item(
            message_ref="gmail:message:abc",
            thread_key="hydrotester-yaxing",
            decision_relevant=True,
            external_reply_needed=True,
        ),
        ci_failure_work_item(run_ref="github:actions:123", branch_key="autonomy-fabric"),
        research_signal_work_item(
            source_ref="paper:example",
            topic_key="agent-evals",
            decision_relevant=True,
        ),
        backup_due_work_item(source_ref="notion:command-center", scope_key="command-center"),
        plugin_candidate_work_item(source_ref="plugin:catalog:example", plugin_key="security-tool"),
    )
    plan = plan_autonomy(tasks, capabilities())
    runnable_ids = {item.task.task_id for item in plan.runnable}
    assert "reply-review:hydrotester-yaxing" in runnable_ids
    assert "ci-failure:autonomy-fabric" in runnable_ids
    assert "research:agent-evals" in runnable_ids
    assert "backup:command-center" in runnable_ids
    assert "plugin-review:security-tool" in runnable_ids
    assert plan.human_gated == ()


def test_plugin_review_and_plugin_connection_are_separate_gates():
    plan = plan_autonomy(
        (
            plugin_candidate_work_item(
                source_ref="plugin:catalog:example",
                plugin_key="security-tool",
            ),
            plugin_connect_work_item(
                source_ref="review:security-tool:approved-candidate",
                plugin_key="security-tool",
            ),
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
