from dataclasses import replace
from datetime import datetime, timedelta, timezone

from nexus_core.outreach_controller import (
    OutreachBatch,
    OutreachTarget,
    PreparedFollowUp,
    PreparedMessage,
    authorize_outreach_release,
    outreach_action_id,
)
from nexus_core.policy import ActionApproval


def test_batch_approval_must_not_preapprove_future_followups() -> None:
    created = datetime(2026, 8, 21, 7, 0, tzinfo=timezone.utc)
    target = OutreachTarget(
        target_id="t1",
        company_name="Example Steel",
        recipient="buyer@example.com",
        role="Procurement Manager",
        channel="email",
        company_fit_refs=("exa:fit:1",),
        need_evidence_refs=("notion:need:1",),
        contact_path_refs=("web:contact:1",),
    )
    batch = OutreachBatch(
        batch_id="batch-per-send-001",
        campaign_ref="security-regression",
        created_at=created.isoformat(),
        expires_at=(created + timedelta(hours=2)).isoformat(),
        source_version_refs=("github:pr13@2c58ea6c",),
        targets=(target,),
        messages=(PreparedMessage("t1", "Initial", "Initial reviewed message."),),
        followups=(PreparedFollowUp("t1", 1, 72, "Re: Initial", "Future follow-up."),),
    )

    approval = ActionApproval(action_id=outreach_action_id(batch), approved=True)
    release = authorize_outreach_release(
        batch,
        approval=approval,
        now=created + timedelta(minutes=10),
    )

    assert release.gate.allowed_now
    assert release.approved_message_ids == ("t1:initial",)
