from dataclasses import replace
from datetime import datetime, timedelta, timezone

from nexus_core.commercial_autonomy import (
    CommercialAction,
    CommercialMandate,
    DealDecisionPacket,
    authorize_final_deal,
    choose_next_commercial_action,
    commercial_mandate_digest,
    evaluate_commercial_action,
    final_deal_action_id,
    mandate_action_id,
    ready_for_final_decision,
    validate_commercial_mandate,
)
from nexus_core.policy import ActionApproval


def _mandate() -> CommercialMandate:
    created = datetime(2026, 8, 19, 20, 0, tzinfo=timezone.utc)
    return CommercialMandate(
        mandate_id="mandate-kcl-001",
        project_ref="project:kcl",
        campaign_ref="campaign:kcl-qualified-buyers",
        created_at=created.isoformat(),
        expires_at=(created + timedelta(days=7)).isoformat(),
        source_version_refs=("notion:resume:v1", "github:pr13@head"),
        allowed_channels=("email", "linkedin"),
        allowed_product_refs=("product:kcl-mop-white-fine-k2o62",),
        max_targets=100,
        max_messages_per_target=4,
        allow_nonbinding_negotiation=True,
    )


def _approval(mandate: CommercialMandate) -> ActionApproval:
    return ActionApproval(action_id=mandate_action_id(mandate), approved=True)


def _message_action(kind: str = "send_intro", ordinal: int = 1) -> CommercialAction:
    return CommercialAction(
        action_id=f"action:{kind}:{ordinal}",
        kind=kind,  # type: ignore[arg-type]
        target_ref="target:buyer-1",
        project_ref="project:kcl",
        campaign_ref="campaign:kcl-qualified-buyers",
        channel="email",
        message_ordinal=ordinal,
        content_digest="sha256:prepared-message-v1",
    )


def _packet(*, recommendation: str = "deal", open_issues: tuple[str, ...] = ()) -> DealDecisionPacket:
    return DealDecisionPacket(
        packet_id="deal-packet-001",
        project_ref="project:kcl",
        counterparty_ref="counterparty:buyer-1",
        source_version_refs=("gmail:thread:v9", "notion:commercial:v4"),
        technical_fit_refs=("evidence:spec-match",),
        commercial_terms_refs=("evidence:quote-7",),
        compliance_refs=("evidence:compliance-check",),
        risk_refs=("evidence:risk-review",),
        open_issue_refs=open_issues,
        recommendation=recommendation,  # type: ignore[arg-type]
    )


def test_exact_mandate_allows_routine_external_outreach_without_per_message_approval() -> None:
    mandate = _mandate()
    decision = evaluate_commercial_action(
        mandate,
        _approval(mandate),
        _message_action("send_intro", 1),
        now=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
    )
    assert decision.allowed_now
    assert not decision.requires_final_deal_gate


def test_mandate_mutation_invalidates_previous_approval() -> None:
    mandate = _mandate()
    approval = _approval(mandate)
    changed = replace(mandate, max_messages_per_target=5)
    assert commercial_mandate_digest(changed) != commercial_mandate_digest(mandate)
    decision = evaluate_commercial_action(
        changed,
        approval,
        _message_action(),
        now=datetime(2026, 8, 20, 12, 0, tzinfo=timezone.utc),
    )
    assert not decision.allowed_now
    assert "exact mandate digest" in decision.reason


def test_expired_mandate_blocks_routine_send() -> None:
    mandate = _mandate()
    decision = evaluate_commercial_action(
        mandate,
        _approval(mandate),
        _message_action(),
        now=datetime(2026, 9, 1, 0, 0, tzinfo=timezone.utc),
    )
    assert not decision.allowed_now
    assert "expired" in decision.reason


def test_project_and_campaign_scope_cannot_bleed() -> None:
    mandate = _mandate()
    approval = _approval(mandate)
    outside_project = replace(_message_action(), project_ref="project:other")
    outside_campaign = replace(_message_action(), campaign_ref="campaign:other")
    assert not evaluate_commercial_action(mandate, approval, outside_project).allowed_now
    assert not evaluate_commercial_action(mandate, approval, outside_campaign).allowed_now


def test_message_count_and_channel_are_bounded_by_mandate() -> None:
    mandate = _mandate()
    approval = _approval(mandate)
    too_many = _message_action("send_followup", 5)
    wrong_channel = replace(_message_action(), channel="whatsapp")
    assert not evaluate_commercial_action(mandate, approval, too_many).allowed_now
    assert not evaluate_commercial_action(mandate, approval, wrong_channel).allowed_now


def test_nonbinding_negotiation_is_autonomous_only_when_enabled() -> None:
    mandate = _mandate()
    action = _message_action("nonbinding_negotiate", 2)
    assert evaluate_commercial_action(mandate, _approval(mandate), action).allowed_now

    disabled = replace(mandate, allow_nonbinding_negotiation=False)
    disabled_approval = _approval(disabled)
    decision = evaluate_commercial_action(disabled, disabled_approval, action)
    assert not decision.allowed_now
    assert "disabled" in decision.reason


def test_binding_actions_always_stop_at_final_deal_gate() -> None:
    mandate = _mandate()
    approval = _approval(mandate)
    for kind in ("accept_offer", "issue_po", "sign_contract", "make_payment", "change_bank_details"):
        action = replace(_message_action(), kind=kind, channel=None, message_ordinal=0, content_digest=None)
        decision = evaluate_commercial_action(mandate, approval, action)
        assert not decision.allowed_now
        assert decision.requires_final_deal_gate


def test_ready_for_final_decision_requires_complete_evidence_and_no_open_issues() -> None:
    assert ready_for_final_decision(_packet())
    assert not ready_for_final_decision(_packet(open_issues=("issue:payment-term",)))
    assert not ready_for_final_decision(_packet(recommendation="conditional"))
    assert not ready_for_final_decision(_packet(recommendation="insufficient_evidence"))


def test_final_deal_approval_is_packet_and_decision_specific() -> None:
    packet = _packet()
    action_id = final_deal_action_id(packet, "deal")
    approved = authorize_final_deal(packet, "deal", approval=ActionApproval(action_id=action_id, approved=True))
    assert approved.gate.allowed_now

    wrong_decision_approval = ActionApproval(action_id=final_deal_action_id(packet, "no_deal"), approved=True)
    blocked = authorize_final_deal(packet, "deal", approval=wrong_decision_approval)
    assert not blocked.gate.allowed_now
    assert blocked.gate.requires_human_approval


def test_commercial_queue_prioritizes_evidence_before_outreach_and_negotiation() -> None:
    actions = (
        _message_action("nonbinding_negotiate", 2),
        replace(_message_action(), action_id="action:qualify", kind="qualify", channel=None, message_ordinal=0, content_digest=None),
        replace(_message_action(), action_id="action:draft", kind="draft", channel=None, message_ordinal=0, content_digest=None),
    )
    chosen = choose_next_commercial_action(actions)
    assert chosen is not None
    assert chosen.kind == "qualify"


def test_mandate_rejects_unsafe_unbounded_limits() -> None:
    mandate = replace(_mandate(), max_targets=10_000, max_messages_per_target=99)
    errors = validate_commercial_mandate(mandate)
    assert "max_targets is outside allowed bounds" in errors
    assert "max_messages_per_target is outside allowed bounds" in errors
