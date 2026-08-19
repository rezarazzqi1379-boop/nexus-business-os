from nexus_core.audit_events import AuditEvent, validate_audit_trace


def _event(
    event_id: str,
    event_type: str,
    *,
    parent_event_id: str = "",
    action_ref: str = "",
    result_class: str = "observed",
    privacy_mode: str = "metadata_only",
):
    return AuditEvent(
        event_id=event_id,
        trace_id="trace:hydrotester-rfq:2026-08-19",
        event_type=event_type,  # type: ignore[arg-type]
        occurred_at="2026-08-19T14:30:00+00:00",
        actor_type="system",
        subject_ref="project:hydrotester",
        result_class=result_class,  # type: ignore[arg-type]
        privacy_mode=privacy_mode,  # type: ignore[arg-type]
        parent_event_id=parent_event_id,
        action_ref=action_ref,
        evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
        correlation_refs=("github:pr:6",),
        tags=("shadow",),
    )


def test_hydrotester_control_chain_is_valid_without_sensitive_payloads():
    events = (
        _event("event:evidence", "evidence_observed"),
        _event(
            "event:decision",
            "decision_recorded",
            parent_event_id="event:evidence",
            result_class="accepted",
        ),
        _event(
            "event:eval",
            "evaluation_completed",
            parent_event_id="event:decision",
            result_class="passed",
        ),
        _event(
            "event:promotion",
            "promotion_decided",
            parent_event_id="event:eval",
            result_class="blocked",
        ),
        _event(
            "event:gate",
            "human_gate_evaluated",
            parent_event_id="event:promotion",
            action_ref="send:hydrotester-final-rfq",
            result_class="blocked",
            privacy_mode="sensitive_omitted",
        ),
    )

    result = validate_audit_trace(events)
    assert result.valid is True
    assert result.errors == ()


def test_action_bound_events_require_exact_action_reference():
    event = _event("event:gate", "human_gate_evaluated", result_class="blocked")
    assert "human_gate_evaluated requires action_ref" in event.validate()


def test_parent_must_exist_inside_trace_set():
    result = validate_audit_trace(
        (_event("event:eval", "evaluation_completed", parent_event_id="event:missing"),)
    )
    assert result.valid is False
    assert any("parent_event_id must reference an event in the trace set" in error for error in result.errors)


def test_parent_cannot_cross_trace_boundary():
    parent = _event("event:one", "evidence_observed")
    child = AuditEvent(
        event_id="event:two",
        trace_id="trace:other",
        event_type="decision_recorded",
        occurred_at="2026-08-19T14:31:00+00:00",
        actor_type="system",
        subject_ref="project:hydrotester",
        result_class="accepted",
        parent_event_id="event:one",
    )
    result = validate_audit_trace((parent, child))
    assert result.valid is False
    assert any("parent_event_id must stay within the same trace_id" in error for error in result.errors)


def test_parent_cycles_fail_closed():
    one = _event("event:one", "decision_recorded", parent_event_id="event:two")
    two = _event("event:two", "evaluation_completed", parent_event_id="event:one")
    result = validate_audit_trace((one, two))
    assert result.valid is False
    assert any("parent chain contains a cycle" in error for error in result.errors)


def test_timestamps_must_be_timezone_aware():
    event = AuditEvent(
        event_id="event:timestamp",
        trace_id="trace:test",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:30:00",
        actor_type="external_source",
        subject_ref="gmail:message:test",
        result_class="observed",
    )
    assert "occurred_at must include a timezone offset" in event.validate()


def test_duplicate_evidence_refs_are_rejected():
    event = AuditEvent(
        event_id="event:refs",
        trace_id="trace:test",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:30:00+00:00",
        actor_type="external_source",
        subject_ref="gmail:message:test",
        result_class="observed",
        evidence_refs=("gmail:message:test", "gmail:message:test"),
    )
    assert "evidence_refs cannot contain duplicates" in event.validate()
