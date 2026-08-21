from datetime import datetime, timedelta, timezone

from nexus_core.outreach_controller import OutreachBatch, OutreachTarget, PreparedFollowUp, PreparedMessage
from nexus_core.outreach_execution import authorize_exact_send, exact_send_action_id
from nexus_core.policy import ActionApproval


def _batch() -> OutreachBatch:
    created = datetime(2026, 8, 21, 7, 0, tzinfo=timezone.utc)
    target = OutreachTarget("t1", "Example Steel", "buyer@example.com", "Procurement Manager", "email", ("exa:fit:1",), ("notion:need:1",), ("web:contact:1",))
    return OutreachBatch(
        "batch-exact-001", "security-regression", created.isoformat(),
        (created + timedelta(hours=2)).isoformat(), ("github:pr13@2c58ea6c",),
        (target,), (PreparedMessage("t1", "Initial", "Initial reviewed message."),),
        (PreparedFollowUp("t1", 1, 72, "Re: Initial", "Future follow-up."),),
    )


def test_initial_approval_does_not_authorize_followup() -> None:
    batch = _batch()
    initial_id = "t1:initial"
    followup_id = "t1:followup:1"
    approval = ActionApproval(action_id=exact_send_action_id(batch, initial_id), approved=True)
    now = datetime(2026, 8, 21, 7, 10, tzinfo=timezone.utc)
    initial = authorize_exact_send(batch, message_id=initial_id, approval=approval, now=now)
    followup = authorize_exact_send(batch, message_id=followup_id, approval=approval, now=now)
    assert initial.gate.allowed_now
    assert not followup.gate.allowed_now
    assert followup.gate.requires_human_approval


def test_followup_requires_its_own_exact_approval() -> None:
    batch = _batch()
    message_id = "t1:followup:1"
    approval = ActionApproval(action_id=exact_send_action_id(batch, message_id), approved=True)
    release = authorize_exact_send(batch, message_id=message_id, approval=approval, now=datetime(2026, 8, 21, 7, 10, tzinfo=timezone.utc))
    assert release.gate.allowed_now


def test_reply_observed_blocks_even_matching_followup_approval() -> None:
    batch = _batch()
    message_id = "t1:followup:1"
    approval = ActionApproval(action_id=exact_send_action_id(batch, message_id), approved=True)
    release = authorize_exact_send(batch, message_id=message_id, approval=approval, now=datetime(2026, 8, 21, 7, 10, tzinfo=timezone.utc), reply_observed=True)
    assert not release.gate.allowed_now
    assert release.gate.requires_human_approval
