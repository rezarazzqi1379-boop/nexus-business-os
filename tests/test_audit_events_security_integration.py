from nexus_core.audit_events import AuditEvent, validate_audit_trace


def test_integration_rejects_unicode_formatting_in_reference_metadata():
    event = AuditEvent(
        event_id="event:unicode-injection",
        trace_id="trace:test",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:30:00+00:00",
        actor_type="external_source",
        subject_ref="gmail:message:test",
        result_class="observed",
        evidence_refs=("gmail:message:test\u2028hidden-line", "ref:\u202esecret"),
    )
    result = validate_audit_trace((event,))
    assert result.valid is False
    assert result.errors.count(
        "event[event:unicode-injection]: evidence_refs cannot contain control or formatting characters"
    ) == 2


def test_integration_malformed_runtime_metadata_returns_errors_not_exceptions():
    event = AuditEvent(
        event_id=123,  # type: ignore[arg-type]
        trace_id="trace:test",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:30:00+00:00",
        actor_type="external_source",
        subject_ref="gmail:message:test",
        result_class="observed",
        evidence_refs=(42,),  # type: ignore[arg-type]
    )
    result = validate_audit_trace((event,))
    assert result.valid is False
    assert any("event_id must be a string" in error for error in result.errors)
    assert any("evidence_refs must be a string" in error for error in result.errors)


def test_integration_non_event_input_fails_closed():
    result = validate_audit_trace(("not-an-event",))  # type: ignore[arg-type]
    assert result.valid is False
    assert "event[0]: must be an AuditEvent" in result.errors
