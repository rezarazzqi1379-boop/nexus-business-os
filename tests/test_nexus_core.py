from nexus_core.capabilities import (
    Capability,
    CapabilityNeed,
    plan_capabilities,
    validate_capabilities,
)
from nexus_core.policy import ActionIntent, evaluate_action


def _capability(
    capability_id: str,
    *,
    status: str = "available",
    can_write: bool = True,
    approval_mode: str = "none",
) -> Capability:
    return Capability(
        capability_id=capability_id,
        purpose=f"Purpose for {capability_id}",
        systems=(capability_id.split(".")[0],),
        can_read=True,
        can_write=can_write,
        status=status,  # type: ignore[arg-type]
        approval_mode=approval_mode,  # type: ignore[arg-type]
        proof_ref=f"proof:{capability_id}" if status in {"available", "degraded"} else "",
    )


def test_available_capability_is_selected_before_degraded():
    capabilities = [
        _capability("supabase.read", status="degraded", can_write=False),
        _capability("notion.read", status="available", can_write=False),
    ]
    plan = plan_capabilities(
        [
            CapabilityNeed(
                need_id="runtime_context",
                purpose="Read structured operating context",
                acceptable_capability_ids=("supabase.read", "notion.read"),
            )
        ],
        capabilities,
    )
    assert [item.capability_id for item in plan.selected] == ["notion.read"]
    assert plan.unresolved_need_ids == ()


def test_blocked_capability_does_not_resolve_need():
    plan = plan_capabilities(
        [
            CapabilityNeed(
                need_id="database_sync",
                purpose="Write runtime rows",
                acceptable_capability_ids=("supabase.write",),
                write_required=True,
            )
        ],
        [_capability("supabase.write", status="blocked")],
    )
    assert plan.selected == ()
    assert plan.unresolved_need_ids == ("database_sync",)


def test_external_write_approval_is_surfaced_by_capability_plan():
    plan = plan_capabilities(
        [
            CapabilityNeed(
                need_id="supplier_reply",
                purpose="Send supplier email",
                acceptable_capability_ids=("gmail.send",),
                write_required=True,
            )
        ],
        [
            _capability(
                "gmail.send",
                approval_mode="human_before_external_write",
            )
        ],
    )
    assert plan.approval_required_capability_ids == ("gmail.send",)


def test_duplicate_capability_id_is_rejected():
    capability = _capability("github.code")
    errors = validate_capabilities([capability, capability])
    assert "duplicate capability_id: github.code" in errors


def test_available_capability_requires_proof_ref():
    capability = Capability(
        capability_id="github.code",
        purpose="Version-controlled code",
        systems=("github",),
        can_read=True,
        can_write=True,
        status="available",
        proof_ref="",
    )
    assert "capability github.code needs proof_ref when status is available" in validate_capabilities(
        [capability]
    )


def test_reversible_branch_commit_is_allowed_without_separate_approval():
    decision = evaluate_action(
        ActionIntent(
            action_id="code-1",
            kind="branch_commit",
            description="Commit tested code to a feature branch",
        )
    )
    assert decision.allowed_now is True
    assert decision.requires_human_approval is False


def test_external_send_requires_human_approval():
    decision = evaluate_action(
        ActionIntent(
            action_id="email-1",
            kind="send_external_message",
            description="Send commercial reply to supplier",
        )
    )
    assert decision.allowed_now is False
    assert decision.requires_human_approval is True


def test_production_deploy_requires_human_approval():
    decision = evaluate_action(
        ActionIntent(
            action_id="deploy-1",
            kind="production_deploy",
            description="Deploy current NEXUS code to production",
        )
    )
    assert decision.allowed_now is False
    assert decision.requires_human_approval is True


def test_human_approval_unlocks_gated_action():
    decision = evaluate_action(
        ActionIntent(
            action_id="merge-1",
            kind="merge_code",
            description="Merge reviewed feature branch to main",
        ),
        human_approved=True,
    )
    assert decision.allowed_now is True
    assert decision.requires_human_approval is False
