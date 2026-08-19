from datetime import datetime, timezone

from nexus_core.durable_workflow import WorkflowState, can_transition, digest_payload, is_replay_equivalent


def state(**overrides):
    base = dict(
        workflow_id="wf-1",
        workflow_type="commercial_outreach",
        state="running",
        sequence=1,
        idempotency_key="idem-1",
        payload_digest=digest_payload("payload-a"),
        source_version_ref="gmail:thread-1:v1",
        updated_at=datetime(2026, 8, 19, 20, 0, tzinfo=timezone.utc),
    )
    base.update(overrides)
    return WorkflowState(**base)


def test_monotonic_transition_is_allowed():
    current = state()
    candidate = state(
        state="waiting_external",
        sequence=2,
        idempotency_key="idem-2",
        payload_digest=digest_payload("payload-b"),
        source_version_ref="gmail:thread-1:v2",
        updated_at=datetime(2026, 8, 19, 20, 1, tzinfo=timezone.utc),
    )
    allowed, errors = can_transition(current, candidate)
    assert allowed is True
    assert errors == ()


def test_out_of_order_sequence_fails_closed():
    allowed, errors = can_transition(state(), state(sequence=3, updated_at=datetime(2026, 8, 19, 20, 1, tzinfo=timezone.utc)))
    assert allowed is False
    assert "non_monotonic_sequence" in errors


def test_same_idempotency_key_cannot_hide_changed_payload():
    current = state()
    candidate = state(
        state="waiting_retry",
        sequence=2,
        payload_digest=digest_payload("different"),
        updated_at=datetime(2026, 8, 19, 20, 1, tzinfo=timezone.utc),
    )
    allowed, errors = can_transition(current, candidate)
    assert allowed is False
    assert "idempotency_payload_mismatch" in errors


def test_terminal_workflow_does_not_reopen_implicitly():
    current = state(state="completed")
    candidate = state(state="running", sequence=2, idempotency_key="idem-2", updated_at=datetime(2026, 8, 19, 20, 1, tzinfo=timezone.utc))
    allowed, errors = can_transition(current, candidate)
    assert allowed is False
    assert "terminal_state_reopen" in errors


def test_replay_equivalence_requires_exact_source_version():
    a = state()
    b = state(source_version_ref="gmail:thread-1:v2")
    assert is_replay_equivalent(a, b) is False
