from nexus_core.autonomy import WorkItem, plan_autonomy
from nexus_core.capabilities import Capability


def capabilities():
    return (
        Capability("gmail.read", "Read Gmail", ("gmail",), True, False, "available", proof_ref="connector:gmail"),
        Capability("github.write", "Write feature-branch code", ("github",), True, True, "available", proof_ref="connector:github"),
        Capability("notion.write", "Write internal knowledge records", ("notion",), True, True, "available", proof_ref="connector:notion"),
        Capability("plugin.manage", "Change connector/plugin access", ("plugins",), True, True, "available", approval_mode="human_before_external_write", proof_ref="connector:plugin-management"),
    )


def test_read_only_monitoring_and_internal_branch_work_can_run():
    plan = plan_autonomy(
        (
            WorkItem("monitor-inbox", "inbox_monitoring", "Read new procurement replies and classify decision-relevant changes.", "read", ("gmail.read",), ("gmail:inbox",), value="high", urgency="high", evidence="strong", cost="low"),
            WorkItem("harden-code", "security", "Create a reversible feature-branch hardening commit.", "branch_commit", ("github.write",), ("github:repo:nexus-business-os",), value="high", urgency="medium", evidence="strong", cost="medium", write_required=True),
        ),
        capabilities(),
    )
    assert [item.task.task_id for item in plan.runnable] == ["monitor-inbox", "harden-code"]
    assert plan.human_gated == ()
    assert plan.blocked == ()


def test_plugin_or_connector_permission_change_requires_human_gate():
    plan = plan_autonomy(
        (
            WorkItem("connect-new-plugin", "innovation", "Connect a new plugin after capability review.", "change_access", ("plugin.manage",), ("plugin:candidate:security-tool",), write_required=True),
        ),
        capabilities(),
    )
    assert plan.runnable == ()
    assert len(plan.human_gated) == 1
    assert plan.human_gated[0].gate.requires_human_approval is True


def test_external_customer_outreach_is_never_auto_authorized():
    plan = plan_autonomy(
        (
            WorkItem("send-prospect-email", "customer_network", "Send a prospecting email to a newly qualified buyer.", "send_external_message", ("notion.write",), ("research:buyer:example",), value="high", urgency="medium", evidence="partial", cost="low", write_required=True),
        ),
        capabilities(),
    )
    assert len(plan.human_gated) == 1
    assert plan.human_gated[0].gate.allowed_now is False


def test_unavailable_capability_remains_blocked_instead_of_being_invented():
    plan = plan_autonomy(
        (
            WorkItem("scan-datacenter-feed", "market_intelligence", "Read a specialized datacenter market feed.", "research", ("datacenter.feed",), ("idea:datacenter-monitoring",), evidence="weak", cost="high"),
        ),
        capabilities(),
    )
    assert len(plan.blocked) == 1
    assert "scan-datacenter-feed" in plan.blocked[0].blockers


def test_priority_is_ordinal_and_deterministic_without_fake_numeric_scores():
    plan = plan_autonomy(
        (
            WorkItem("low-value", "research", "Read a low-priority background source.", "research", ("gmail.read",), ("source:low",), value="low", urgency="low", evidence="strong", cost="low"),
            WorkItem("high-value", "research", "Read a decision-critical source.", "research", ("gmail.read",), ("source:high",), value="critical", urgency="high", evidence="strong", cost="low"),
        ),
        capabilities(),
    )
    assert [item.task.task_id for item in plan.runnable] == ["high-value", "low-value"]


def test_malformed_metadata_fails_closed():
    plan = plan_autonomy(
        (WorkItem("bad\u202eid", "research", "Research safely.", "research", ("gmail.read",), ("source:test",)),),
        capabilities(),
    )
    assert len(plan.blocked) == 1
    assert any("control or formatting" in blocker for blocker in plan.blocked[0].blockers)
