from dataclasses import replace

from nexus_security.exact_external_gate import ExactApproval, ExactExternalMessage, authorize_exact_external_message, exact_external_action_id


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


def test_exact_send_blocked_without_approval():
    release = authorize_exact_external_message(_message())
    assert release.action_id
    assert release.gate.allowed_now is False
    assert release.gate.requires_human_approval is True


def test_exact_matching_approval_allows_only_snapshot():
    message = _message()
    action_id = exact_external_action_id(message)
    release = authorize_exact_external_message(message, approval=ExactApproval(action_id=action_id, approved=True))
    assert release.gate.allowed_now is True


def test_content_recipient_attachment_or_source_change_invalidates_approval():
    original = _message()
    approval = ExactApproval(action_id=exact_external_action_id(original), approved=True)
    variants = (
        _message(body="Please confirm final technical specification and price."),
        _message(recipient="engineering@example.com"),
        _message(attachment_refs=("drive:rfq-rev1.3",)),
        _message(source_version_refs=("gmail:thread-42:v4", "project:hydrotester:rev1.3")),
    )
    for changed in variants:
        release = authorize_exact_external_message(changed, approval=approval)
        assert release.gate.allowed_now is False
        assert release.action_id != approval.action_id


def test_initial_approval_cannot_preapprove_followup():
    initial = _message()
    approval = ExactApproval(action_id=exact_external_action_id(initial), approved=True)
    followup = _message(
        message_id="supplier-42:followup:1",
        subject="Follow-up: technical clarification",
        body="Following up on the technical clarification request.",
        source_version_refs=("gmail:thread-42:v4", "project:hydrotester:rev1.2"),
    )
    release = authorize_exact_external_message(followup, approval=approval)
    assert release.gate.allowed_now is False
    assert release.action_id != approval.action_id


def test_truthy_non_boolean_approval_fails_closed():
    message = _message()
    approval = ExactApproval(action_id=exact_external_action_id(message), approved=1)
    release = authorize_exact_external_message(message, approval=approval)
    assert release.gate.allowed_now is False


def test_malformed_control_metadata_and_unhashable_ref_fail_closed():
    malformed = _message(message_id="supplier-42:\u202efollowup")
    release = authorize_exact_external_message(malformed)
    assert release.action_id == ""
    assert release.gate.allowed_now is False

    malformed_ref = _message(source_version_refs=("gmail:thread-42:v3", ["not", "string"]))
    release = authorize_exact_external_message(malformed_ref)
    assert release.action_id == ""
    assert release.gate.allowed_now is False
    assert "source_version_refs must be a string" in release.gate.reason


def test_duplicate_refs_fail_closed():
    release = authorize_exact_external_message(_message(source_version_refs=("x", "x")))
    assert release.action_id == ""
    assert release.gate.allowed_now is False
