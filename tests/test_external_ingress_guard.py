from pathlib import Path

import pytest

from approvals import ApprovalStore
from nexus_security.external_ingress_guard import (
    ExternalMessageIngress,
    approval_request_for_reply,
    build_review_descriptor,
    ingest_external_message,
)


def make_ingress(**overrides):
    kwargs = dict(
        source_ref="whatsapp:+98912xxxxxxx",
        thread_key="thread-supplier-42",
        raw_content="Please confirm the delivery date for order 42.",
        decision_relevant=True,
        external_reply_needed=True,
    )
    kwargs.update(overrides)
    return ingest_external_message(**kwargs)


# ---------------------------------------------------------------------------
# ingest_external_message
# ---------------------------------------------------------------------------

def test_ingest_hashes_content_and_round_trips_metadata():
    ingress = make_ingress()
    assert ingress.source_ref == "whatsapp:+98912xxxxxxx"
    assert ingress.thread_key == "thread-supplier-42"
    assert ingress.decision_relevant is True
    assert ingress.external_reply_needed is True
    assert len(ingress.content_sha256) == 64
    # same content -> same hash, deterministic
    again = make_ingress()
    assert again.content_sha256 == ingress.content_sha256


def test_ingest_different_content_different_hash():
    a = make_ingress(raw_content="Order 42 ships Monday.")
    b = make_ingress(raw_content="Order 42 ships Tuesday.")
    assert a.content_sha256 != b.content_sha256


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_ref", ""),
        ("source_ref", "   "),
        ("source_ref", "x" * 257),
        ("source_ref", " leading-space"),
        ("thread_key", ""),
        ("thread_key", "x" * 257),
    ],
)
def test_ingest_rejects_unsafe_metadata_fields(field, value):
    with pytest.raises(ValueError):
        make_ingress(**{field: value})


def test_ingest_rejects_oversized_raw_content():
    with pytest.raises(ValueError):
        make_ingress(raw_content="x" * 100_001)


def test_ingest_rejects_control_characters_in_source_ref():
    with pytest.raises(ValueError):
        make_ingress(source_ref="whatsapp:+98\x00912")


@pytest.mark.parametrize("field", ["decision_relevant", "external_reply_needed"])
def test_ingest_rejects_non_bool_flags(field):
    with pytest.raises(ValueError):
        make_ingress(**{field: "yes"})


def test_ingest_rejects_non_string_raw_content():
    with pytest.raises(ValueError):
        make_ingress(raw_content=12345)


# ---------------------------------------------------------------------------
# build_review_descriptor
# ---------------------------------------------------------------------------

def test_build_review_descriptor_never_authorizes_action():
    ingress = make_ingress()
    descriptor = build_review_descriptor(ingress)
    assert descriptor["external_action_authorized"] is False
    assert descriptor["action_kind"] == "review_and_draft"
    assert descriptor["thread_key"] == ingress.thread_key
    assert descriptor["source_ref"] == ingress.source_ref
    assert descriptor["content_sha256"] == ingress.content_sha256
    assert descriptor["decision_relevant"] is True
    assert descriptor["external_reply_needed"] is True
    assert descriptor["task_id"] == f"reply-review:{ingress.thread_key}"


def test_build_review_descriptor_rejects_wrong_type():
    with pytest.raises(ValueError):
        build_review_descriptor("not-an-ingress")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# approval_request_for_reply
# ---------------------------------------------------------------------------

def make_approval_request(ingress=None, **overrides):
    ingress = ingress or make_ingress()
    kwargs = dict(
        project_id="PRJ-FAL-01",
        channel="whatsapp",
        recipient="+98912yyyyyyy",
        subject="",
        reviewed_body="Confirmed: order 42 ships Monday.",
        requested_by="reza",
    )
    kwargs.update(overrides)
    return approval_request_for_reply(ingress, **kwargs)


def test_approval_request_builds_real_scoped_request():
    request = make_approval_request()
    assert request.action == "send_external_message"
    assert request.target == "+98912yyyyyyy"
    assert request.project_id == "PRJ-FAL-01"
    assert request.requested_by == "reza"
    assert request.parameters["channel"] == "whatsapp"
    assert request.parameters["body"] == "Confirmed: order 42 ships Monday."
    assert request.parameters["thread_key"] == "thread-supplier-42"
    assert request.parameters["source_content_sha256"]


def test_approval_request_rejects_invalid_channel():
    with pytest.raises(ValueError):
        make_approval_request(channel="carrier-pigeon")


def test_approval_request_rejects_empty_recipient():
    with pytest.raises(ValueError):
        make_approval_request(recipient="")


def test_approval_request_rejects_oversized_body():
    with pytest.raises(ValueError):
        make_approval_request(reviewed_body="x" * 50_001)


def test_approval_request_rejects_duplicate_attachment_refs():
    with pytest.raises(ValueError):
        make_approval_request(attachment_refs=("doc-1", "doc-1"))


def test_approval_request_rejects_wrong_ingress_type():
    with pytest.raises(ValueError):
        approval_request_for_reply(
            "not-an-ingress",  # type: ignore[arg-type]
            project_id="PRJ-FAL-01",
            channel="whatsapp",
            recipient="+98912yyyyyyy",
            subject="",
            reviewed_body="Body.",
            requested_by="reza",
        )


def test_different_reviewed_body_produces_different_action_digest():
    ingress = make_ingress()
    a = make_approval_request(ingress, reviewed_body="Confirmed: ships Monday.")
    b = make_approval_request(ingress, reviewed_body="Confirmed: ships Tuesday.")
    assert a.action_digest != b.action_digest


def test_different_channel_or_recipient_produces_different_action_digest():
    ingress = make_ingress()
    base = make_approval_request(ingress)
    other_recipient = make_approval_request(ingress, recipient="+98912zzzzzzz")
    other_channel = make_approval_request(ingress, channel="email", recipient="ops@example.com")
    assert base.action_digest != other_recipient.action_digest
    assert base.action_digest != other_channel.action_digest


# ---------------------------------------------------------------------------
# End-to-end: real single-use enforcement via ApprovalStore
#
# This is the point of the rewrite -- the original branch's
# `exact_external_gate.py` had no consumption tracking, so the same
# approval object could authorize more than one send. Routing through the
# real `ApprovalStore` closes that: the same approval can be consumed
# exactly once for its exact scoped action, and a second attempt fails.
# ---------------------------------------------------------------------------

def test_end_to_end_single_use_enforcement(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    ingress = make_ingress()
    request = make_approval_request(ingress)

    approval_id = store.request(request)
    status = store.decide(approval_id, approved=True, decided_by="reza")
    assert status == "approved"

    first = store.consume(approval_id, action_digest=request.action_digest)
    assert first is True

    second = store.consume(approval_id, action_digest=request.action_digest)
    assert second is False


def test_end_to_end_consume_rejects_mismatched_action_digest(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    ingress = make_ingress()
    request = make_approval_request(ingress, reviewed_body="Confirmed: ships Monday.")
    other_request = make_approval_request(ingress, reviewed_body="Confirmed: ships Tuesday.")

    approval_id = store.request(request)
    store.decide(approval_id, approved=True, decided_by="reza")

    # A different reviewed reply (different action_digest) must not be
    # authorized by this approval, even though it targets the same thread.
    mismatched = store.consume(approval_id, action_digest=other_request.action_digest)
    assert mismatched is False

    # The real, matching digest still consumes successfully afterwards.
    matching = store.consume(approval_id, action_digest=request.action_digest)
    assert matching is True


def test_end_to_end_unapproved_request_cannot_be_consumed(tmp_path):
    store = ApprovalStore(tmp_path / "approvals.db")
    request = make_approval_request()
    approval_id = store.request(request)
    # Never decided -- still pending, not approved.
    consumed = store.consume(approval_id, action_digest=request.action_digest)
    assert consumed is False
