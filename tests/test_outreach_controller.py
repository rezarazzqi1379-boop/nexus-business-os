from dataclasses import replace
from datetime import datetime, timedelta, timezone

from nexus_core.outreach_controller import (
    OutreachBatch,
    OutreachTarget,
    PreparedMessage,
    authorize_outreach_release,
    outreach_action_id,
    preview_outreach_release,
    qualified_targets,
    validate_outreach_batch,
)
from nexus_core.policy import ActionApproval


def _target(*, target_id: str = "t1", recipient: str = "buyer@example.com") -> OutreachTarget:
    return OutreachTarget(
        target_id=target_id,
        company_name="Example Steel",
        recipient=recipient,
        role="Procurement Manager",
        channel="email",
        company_fit_refs=("exa:company-fit:1",),
        need_evidence_refs=("notion:project:octg",),
        contact_path_refs=("gmail-or-web:contact:1",),
    )


def _batch() -> OutreachBatch:
    created = datetime(2026, 8, 19, 20, 0, tzinfo=timezone.utc)
    return OutreachBatch(
        batch_id="batch-001",
        campaign_ref="octg-network-pilot",
        created_at=created.isoformat(),
        expires_at=(created + timedelta(hours=2)).isoformat(),
        source_version_refs=("github:pr13@abc", "notion:resume@v1"),
        targets=(_target(),),
        messages=(PreparedMessage("t1", "OCTG equipment sourcing", "Dear Sir or Madam,\n\nWe are evaluating a qualified sourcing route."),),
    )


def test_preview_requires_human_gate_for_external_send() -> None:
    release = preview_outreach_release(_batch())
    assert not release.gate.allowed_now
    assert release.gate.requires_human_approval
    assert release.approved_message_ids == ()


def test_exact_one_click_approval_releases_only_reviewed_batch() -> None:
    batch = _batch()
    approval = ActionApproval(action_id=outreach_action_id(batch), approved=True)
    release = authorize_outreach_release(
        batch,
        approval=approval,
        now=datetime(2026, 8, 19, 20, 30, tzinfo=timezone.utc),
    )
    assert release.gate.allowed_now
    assert release.approved_message_ids == ("t1",)


def test_message_mutation_invalidates_previous_approval() -> None:
    batch = _batch()
    approval = ActionApproval(action_id=outreach_action_id(batch), approved=True)
    changed = replace(
        batch,
        messages=(PreparedMessage("t1", "OCTG equipment sourcing", "Changed body after review"),),
    )
    release = authorize_outreach_release(
        changed,
        approval=approval,
        now=datetime(2026, 8, 19, 20, 30, tzinfo=timezone.utc),
    )
    assert not release.gate.allowed_now
    assert release.gate.requires_human_approval
    assert release.approved_message_ids == ()


def test_recipient_mutation_invalidates_previous_approval() -> None:
    batch = _batch()
    approval = ActionApproval(action_id=outreach_action_id(batch), approved=True)
    changed = replace(batch, targets=(_target(recipient="other@example.com"),))
    release = authorize_outreach_release(
        changed,
        approval=approval,
        now=datetime(2026, 8, 19, 20, 30, tzinfo=timezone.utc),
    )
    assert not release.gate.allowed_now
    assert release.approved_message_ids == ()


def test_expired_batch_cannot_be_released_even_with_matching_approval() -> None:
    batch = _batch()
    approval = ActionApproval(action_id=outreach_action_id(batch), approved=True)
    release = authorize_outreach_release(
        batch,
        approval=approval,
        now=datetime(2026, 8, 19, 23, 0, tzinfo=timezone.utc),
    )
    assert not release.gate.allowed_now
    assert release.gate.requires_human_approval
    assert "expired" in release.gate.reason


def test_every_target_requires_exactly_one_message() -> None:
    batch = replace(_batch(), messages=())
    errors = validate_outreach_batch(batch)
    assert "messages requires at least one prepared message" in errors


def test_duplicate_recipient_is_rejected() -> None:
    target2 = _target(target_id="t2")
    batch = replace(
        _batch(),
        targets=(_target(), target2),
        messages=(
            PreparedMessage("t1", "Subject 1", "Body 1"),
            PreparedMessage("t2", "Subject 2", "Body 2"),
        ),
    )
    assert "duplicate recipient/channel pair" in validate_outreach_batch(batch)


def test_qualified_targets_require_fit_need_and_contact_evidence() -> None:
    good = _target()
    weak = replace(good, target_id="t2", recipient="weak@example.com", need_evidence_refs=())
    duplicate = replace(good, target_id="t3")
    assert qualified_targets((good, weak, duplicate)) == (good,)
