import pytest

from nexus_control_plane.exact_send import ExactSendApproval, authorize_exact_send, exact_send_action_id


def _action(message_id: str, body: str = "Hello") -> str:
    return exact_send_action_id(
        batch_id="batch-1",
        message_id=message_id,
        target="supplier@example.com",
        subject="RFQ follow-up",
        body=body,
        source_version_refs=("rfq-v1",),
        thread_ref="thread-1",
    )


def test_matching_approval_allows_only_exact_send():
    action = _action("supplier:initial")
    decision = authorize_exact_send(action_id=action, approval=ExactSendApproval(action))
    assert decision.allowed is True
    assert decision.requires_human_approval is False


def test_initial_approval_does_not_authorize_future_followup():
    initial = _action("supplier:initial")
    followup = _action("supplier:followup:1")
    decision = authorize_exact_send(action_id=followup, approval=ExactSendApproval(initial))
    assert decision.allowed is False
    assert decision.requires_human_approval is True


def test_editing_message_invalidates_prior_approval():
    original = _action("supplier:initial", body="Hello")
    edited = _action("supplier:initial", body="Hello — revised")
    assert original != edited
    decision = authorize_exact_send(action_id=edited, approval=ExactSendApproval(original))
    assert decision.allowed is False


def test_missing_or_denied_approval_fails_closed():
    action = _action("supplier:initial")
    assert authorize_exact_send(action_id=action, approval=None).allowed is False
    assert authorize_exact_send(action_id=action, approval=ExactSendApproval(action, approved=False)).allowed is False


def test_provenance_change_changes_action_id():
    first = exact_send_action_id(
        batch_id="batch-1", message_id="m1", target="a@example.com", subject="S", body="B",
        source_version_refs=("rfq-v1",),
    )
    second = exact_send_action_id(
        batch_id="batch-1", message_id="m1", target="a@example.com", subject="S", body="B",
        source_version_refs=("rfq-v2",),
    )
    assert first != second


def test_multiline_email_body_is_supported_and_still_content_bound():
    multiline = _action("supplier:initial", body="Dear Supplier,\n\nPlease confirm the revised specification.\nRegards,\nReza")
    changed = _action("supplier:initial", body="Dear Supplier,\n\nPlease confirm the revised specification.\nRegards,\nReza R.")
    assert multiline
    assert multiline != changed


def test_normal_tabs_and_crlf_in_body_are_supported():
    action = _action("supplier:initial", body="Line 1\r\nLine 2\tValue")
    assert action.startswith("external-send:")


def test_dangerous_formatting_characters_fail_closed():
    with pytest.raises(ValueError):
        exact_send_action_id(
            batch_id="batch-1", message_id="m1", target="a@example.com", subject="S", body="bad\u202econtent"
        )


def test_subject_newline_fails_closed():
    with pytest.raises(ValueError):
        exact_send_action_id(
            batch_id="batch-1", message_id="m1", target="a@example.com", subject="bad\nsubject", body="safe body"
        )


def test_source_version_refs_reject_plain_string_instead_of_hashing_characters():
    with pytest.raises(ValueError, match="sequence of strings"):
        exact_send_action_id(
            batch_id="batch-1",
            message_id="m1",
            target="a@example.com",
            subject="S",
            body="B",
            source_version_refs="rfq-v1",
        )
