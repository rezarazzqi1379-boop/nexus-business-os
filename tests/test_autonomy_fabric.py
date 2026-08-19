from nexus_core.autonomy import WorkItem, plan_autonomy
from nexus_core.capabilities import Capability


def capabilities():
    return (
        Capability(
            capability_id="gmail.read",
            purpose="Read Gmail",
            systems=("gmail",),
            can_read=True,
            can_write=False,
            status="available",
            proof_ref="connector:gmail",
        ),
        Capability(
            capability_id="github.write",
            purpose="Write feature-branch code",
            systems=("github",),
            can_read=True,
            can_write=True,
            status="available",
            proof_ref="connector:github",
        ),
        Capability(
            capability_id="notion.write",
            purpose="Write internal knowledge records",
            systems=("notion",),
            can_read=True,
            can_write=True,
            status="available",
            proof_ref="connector:notion",
        ),
        Capability(
            capability_id="plugin.manage",
            purpose="Change connector/plugin access",
            systems=("plugins",),
            can_read=True,
            can_write=True,
            status="available",
            approval_mode="human_before_external_write",
            proof_ref="connector:plugin-management",
        ),
    )


def test_read_only_monitoring_and_internal_branch_work_can_run():
    plan = plan_autonomy(
        (
            WorkItem(
                task_id="monitor-inbox",
                domain="inbox_monitoring",
                objective="Read new procurement replies and classify decision-relevant changes.",
                action_kind="read",
                acceptable_capability_ids=("gmail.read",),
                evidence_refs=("gmail:inbox",),
                value="high",
                urgency="high",
                evidence="strong",
                cost="low",
            ),
            WorkItem(
                task_id="harden-code",
                domain="security",
                objective="Create a reversible feature-branch hardening commit.",
                action_kind="branch_commit",
                acceptable_capability_ids=("github.write",),
                evidence_refs=("github:repo:nexus-business-os",),
                value="high",
                urgency="medium",
                evidence="strong",
                cost="medium",
                write_required=True,
            ),
        ),
        capabilities(),
    )
    assert [item.task.task_id for item in plan.runnable] == ["monitor-inbox", "harden-code"]
    assert plan.human_gated == ()
    assert plan.blocked == ()


def test_plugin_or_connector_permission_change_requires_human_gate():
    plan = plan_autonomy(
        (
            WorkItem(
                task_id="connect-new-plugin",
                domain="innovation",
                objective="Connect a new plugin after capability review.",
                action_kind="change_access",
                acceptable_capability_ids=("plugin.manage",),
                evidence_refs=("plugin:candidate:security-tool",),
                value="medium",
                urgency="low",
                evidence="partial",
                cost="medium",
                write_required=True,
            ),
        ),
        capabilities(),
    )
    assert plan.runnable == ()
    assert len(plan.human_gated) == 1
    assert plan.human_gated[0].gate.requires_human_approval is True


def test_external_customer_outreach_is_never_auto_authorized():
    plan = plan_autonomy(
        (
            WorkItem(
                task_id="send-prospect-email",
                domain="customer_network",
                objective="Send a prospecting email to a newly qualified buyer.",
                action_kind="send_external_message",
                acceptable_capability_ids=("notion.write",),
                evidence_refs=("research:buyer:example",),
                value="high",
                urgency="medium",
                evidence="partial",
                cost="low",
                write_required=True,
            ),
        ),
        capabilities(),
    )
    assert len(plan.human_gated) == 1
    assert plan.human_gated[0].gate.allowed_now is False


def test_unavailable_capability_remains_blocked_instead_of_being_invented():
    plan = plan_autonomy(
        (
            WorkItem(
                task_id="scan-datacenter-feed",
                domain="market_intelligence",
                objective="Read a specialized datacenter market feed.",
                action_kind="research",
                acceptable_capability_ids=("datacenter.feed",),
                evidence_refs=("idea:datacenter-monitoring",),
                value="medium",
                urgency="medium",
                evidence="weak",
                cost="high",
            ),
        ),
        capabilities(),
    )
    assert len(plan.blocked) == 1
    assert "scan-datacenter-feed" in plan.blocked[0].blockers


def test_priority_is_ordinal_and_deterministic_without_fake_numeric_scores():
    plan = plan_autonomy(
        (
            WorkItem(
                task_id="low-value",
                domain="research",
                objective="Read a low-priority background source.",
                action_kind="research",
                acceptable_capability_ids=("gmail.read",),
                evidence_refs=("source:low",),
                value="low",
                urgency="low",
                evidence="strong",
                cost="low",
            ),
            WorkItem(
                task_id="high-value",
                domain="research",
                objective="Read a decision-critical source.",
                action_kind="research",
                acceptable_capability_ids=("gmail.read",),
                evidence_refs=("source:high",),
                value="critical",
                urgency="high",
                evidence="strong",
                cost="low",
            ),
        ),
        capabilities(),
    )
    assert [item.task.task_id for item in plan.runnable] == ["high-value", "low-value"]


def test_malformed_metadata_fails_closed():
    plan = plan_autonomy(
        (
            WorkItem(
                task_id="bad\u202eid",
                domain="research",
                objective="Research safely.",
                action_kind="research",
                acceptable_capability_ids=("gmail.read",),
                evidence_refs=("source:test",),
            ),
        ),
        capabilities(),
    )
    assert len(plan.blocked) == 1
    assert any("control or formatting" in blocker for blocker in plan.blocked[0].blockers)
