from dataclasses import replace

from nexus_core.exact_external_action import (
    ExactExternalMessage,
    authorize_exact_external_message,
    exact_external_action_id,
)
from nexus_core.policy import ActionApproval


def _message(**changes):
    base = ExactExternalMessage(
        message_id="supplier-42:initial",
        channel="email",
        recipient="sales@example.com",
        subject="Technical clarification",
        body="Please confirm the final technical specification.",
        source_version_refs=("gmail:thread-42:v3", "project:hydrotester:rev1.2"),
        attachment_refs=("drive:rfq-rev1.2",),
    )
    return replace(base, **changes)


def test_exact_external_send_is_blocked_without_human_approval():
    release = authorize_exact_external_message(_message())
    assert release.action_id
    assert release.gate.allowed_now is False
    assert release.gate.requires_human_approval is True


def test_exact_matching_approval_allows_only_that_message_snapshot():
    message = _message()
    action_id = exact_external_action_id(message)
    release = authorize_exact_external_message(
        message,
        approval=ActionApproval(action_id=action_id, approved=True),
    )
    assert release.gate.allowed_now is True


def test_content_change_invalidates_prior_approval():
    original = _message()
    approval = ActionApproval(action_id=exact_external_action_id(original), approved=True)
    changed = _message(body="Please confirm the final technical specification and price.")
    release = authorize_exact_external_message(changed, approval=approval)
    assert release.gate.allowed_now is False
    assert release.gate.requires_human_approval is True
    assert release.action_id != approval.action_id


def test_recipient_change_invalidates_prior_approval():
    original = _message()
    approval = ActionApproval(action_id=exact_external_action_id(original), approved=True)
    changed = _message(recipient="engineering@example.com")
    release = authorize_exact_external_message(changed, approval=approval)
    assert release.gate.allowed_now is False
    assert release.action_id != approval.action_id


def test_initial_message_approval_cannot_preapprove_future_followup():
    initial = _message()
    approval = ActionApproval(action_id=exact_external_action_id(initial), approved=True)
    followup = _message(
        message_id="supplier-42:followup:1",
        subject="Follow-up: technical clarification",
        body="Following up on the technical clarification request.",
        source_version_refs=("gmail:thread-42:v4", "project:hydrotester:rev1.2"),
    )
    release = authorize_exact_external_message(followup, approval=approval)
    assert release.gate.allowed_now is False
    assert release.gate.requires_human_approval is True
    assert release.action_id != approval.action_id


def test_attachment_or_source_version_change_requires_fresh_approval():
    original = _message()
    approval = ActionApproval(action_id=exact_external_action_id(original), approved=True)

    attachment_change = _message(attachment_refs=("drive:rfq-rev1.3",))
    source_change = _message(source_version_refs=("gmail:thread-42:v4", "project:hydrotester:rev1.3"))

    assert authorize_exact_external_message(attachment_change, approval=approval).gate.allowed_now is False
    assert authorize_exact_external_message(source_change, approval=approval).gate.allowed_now is False


def test_malformed_or_control_character_metadata_fails_closed():
    malformed = _message(message_id="supplier-42:\u202efollowup")
    release = authorize_exact_external_message(malformed)
    assert release.action_id == ""
    assert release.gate.allowed_now is False
    assert release.gate.requires_human_approval is False


def test_unhashable_reference_value_fails_closed_instead_of_crashing():
    malformed = _message(source_version_refs=("gmail:thread-42:v3", ["not", "a", "string"]))
    release = authorize_exact_external_message(malformed)
    assert release.action_id == ""
    assert release.gate.allowed_now is False
    assert release.gate.requires_human_approval is False
    assert "source_version_refs must be a string" in release.gate.reason
