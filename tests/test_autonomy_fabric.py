from hypothesis import given, strategies as st

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


def test_malformed_priority_tier_fails_closed_instead_of_crashing_sort():
    task = WorkItem(
        task_id="bad-priority",
        domain="research",
        objective="Malformed priority must be blocked before execution.",
        action_kind="research",
        acceptable_capability_ids=("gmail.read",),
        evidence_refs=("source:test",),
        value="not-a-tier",  # type: ignore[arg-type]
    )
    plan = plan_autonomy((task,), capabilities())
    assert plan.runnable == ()
    assert len(plan.blocked) == 1
    assert "value must be supported" in plan.blocked[0].blockers


def test_malformed_evidence_tier_fails_closed_before_action_gate():
    task = WorkItem(
        task_id="bad-evidence",
        domain="research",
        objective="Malformed evidence tier must never reach capability execution.",
        action_kind="send_external_message",
        acceptable_capability_ids=("notion.write",),
        evidence_refs=("source:test",),
        evidence=object(),  # type: ignore[arg-type]
        write_required=True,
    )
    plan = plan_autonomy((task,), capabilities())
    assert plan.runnable == ()
    assert plan.human_gated == ()
    assert len(plan.blocked) == 1
    assert "evidence must be supported" in plan.blocked[0].blockers
    assert plan.blocked[0].selected_capability_ids == ()


def test_unsupported_action_kind_is_blocked_before_capability_selection():
    task = WorkItem(
        task_id="bad-action-kind",
        domain="research",
        objective="Malformed action kinds must not reach capability planning.",
        action_kind="invent-permission",  # type: ignore[arg-type]
        acceptable_capability_ids=("github.write",),
        evidence_refs=("source:test",),
        write_required=True,
    )
    plan = plan_autonomy((task,), capabilities())
    assert plan.runnable == ()
    assert plan.human_gated == ()
    assert len(plan.blocked) == 1
    assert "action_kind must be supported" in plan.blocked[0].blockers
    assert plan.blocked[0].selected_capability_ids == ()


@given(st.one_of(st.none(), st.integers(), st.lists(st.text(max_size=5)), st.dictionaries(st.text(max_size=5), st.integers(), max_size=3)))
def test_malformed_action_kind_never_reaches_capability_selection(value):
    task = WorkItem(
        task_id="property-bad-action-kind",
        domain="research",
        objective="Generated malformed action kinds must fail before capability planning.",
        action_kind=value,  # type: ignore[arg-type]
        acceptable_capability_ids=("github.write",),
        evidence_refs=("source:property-test",),
        write_required=True,
    )
    plan = plan_autonomy((task,), capabilities())
    assert plan.runnable == ()
    assert plan.human_gated == ()
    assert len(plan.blocked) == 1
    assert plan.blocked[0].selected_capability_ids == ()
    assert any(blocker.startswith("action_kind") for blocker in plan.blocked[0].blockers)
