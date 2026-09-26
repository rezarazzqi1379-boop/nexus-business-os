from nexus_observability import TraceEvent, validate_trace


def _valid_chain():
    return (
        TraceEvent(
            event_id="event:evidence:1",
            trace_id="trace:hydrotester:1",
            event_type="evidence_read",
            occurred_at="2026-08-19T14:30:00Z",
            actor="nexus:research",
            result="success",
            evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
            correlation_ref="hydrotester:rfq:1",
            attributes={"domain": "procurement", "case_id": "hydrotester:rfq:1"},
        ),
        TraceEvent(
            event_id="event:decision:1",
            trace_id="trace:hydrotester:1",
            event_type="decision_recorded",
            occurred_at="2026-08-19T14:31:00Z",
            actor="nexus:control-plane",
            result="success",
            evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
            parent_event_id="event:evidence:1",
            correlation_ref="hydrotester:rfq:1",
            decision_ref="decision:requirement-readiness:1",
            attributes={"status": "shadow", "critical": True},
        ),
        TraceEvent(
            event_id="event:eval:1",
            trace_id="trace:hydrotester:1",
            event_type="evaluation_completed",
            occurred_at="2026-08-19T14:32:00Z",
            actor="nexus:eval",
            result="failure",
            evidence_refs=("github:pr:2",),
            parent_event_id="event:decision:1",
            correlation_ref="hydrotester:rfq:1",
            eval_ref="eval:requirement-readiness:1",
            attributes={"harness_version": "evaluation-harness-v0.1"},
        ),
        TraceEvent(
            event_id="event:promotion:1",
            trace_id="trace:hydrotester:1",
            event_type="promotion_decided",
            occurred_at="2026-08-19T14:33:00Z",
            actor="nexus:promotion",
            result="blocked",
            evidence_refs=("github:pr:6",),
            parent_event_id="event:eval:1",
            correlation_ref="hydrotester:rfq:1",
            eval_ref="promotion:requirement-readiness:1",
            attributes={"reason_code": "critical_case_failure"},
        ),
        TraceEvent(
            event_id="event:gate:1",
            trace_id="trace:hydrotester:1",
            event_type="approval_decided",
            occurred_at="2026-08-19T14:34:00Z",
            actor="nexus:human-gate",
            result="blocked",
            evidence_refs=("github:pr:4",),
            parent_event_id="event:promotion:1",
            correlation_ref="hydrotester:rfq:1",
            action_ref="send:hydrotester-final-rfq:1",
            attributes={"reversible": False},
        ),
    )


def test_valid_trace_reconstructs_single_chain_without_payloads():
    result = validate_trace(_valid_chain())
    assert result.valid is True
    assert result.errors == ()
    assert result.root_event_ids == ("event:evidence:1",)
    assert result.terminal_event_ids == ("event:gate:1",)


def test_sensitive_attribute_key_is_rejected():
    event = TraceEvent(
        event_id="event:evidence:secret",
        trace_id="trace:secret:1",
        event_type="evidence_read",
        occurred_at="2026-08-19T14:30:00Z",
        actor="nexus:research",
        result="success",
        evidence_refs=("gmail:message:secret",),
        payload_ref="gmail:message:secret",
        attributes={"api_token": "should-never-be-here"},
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("disallowed for privacy" in error for error in result.errors)


def test_arbitrary_attribute_key_is_rejected_even_if_it_looks_harmless():
    event = TraceEvent(
        event_id="event:evidence:metadata",
        trace_id="trace:metadata:1",
        event_type="evidence_read",
        occurred_at="2026-08-19T14:30:00Z",
        actor="nexus:research",
        result="success",
        evidence_refs=("evidence:1",),
        attributes={"freeform_note": "supplier said maybe"},
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("metadata allowlist" in error for error in result.errors)


def test_multiline_attribute_value_is_rejected_to_reduce_payload_leakage():
    event = TraceEvent(
        event_id="event:evidence:metadata",
        trace_id="trace:metadata:1",
        event_type="evidence_read",
        occurred_at="2026-08-19T14:30:00Z",
        actor="nexus:research",
        result="success",
        evidence_refs=("evidence:1",),
        attributes={"status": "line one\nline two"},
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("compact metadata" in error for error in result.errors)


def test_cross_trace_parent_reference_is_rejected():
    first = TraceEvent(
        event_id="event:1",
        trace_id="trace:1",
        event_type="evidence_read",
        occurred_at="2026-08-19T14:30:00Z",
        actor="nexus:research",
        result="success",
        evidence_refs=("evidence:1",),
    )
    second = TraceEvent(
        event_id="event:2",
        trace_id="trace:2",
        event_type="decision_recorded",
        occurred_at="2026-08-19T14:31:00Z",
        actor="nexus:control-plane",
        result="success",
        parent_event_id="event:1",
        decision_ref="decision:1",
    )
    result = validate_trace((first, second))
    assert result.valid is False
    assert "all trace events must share exactly one trace_id" in result.errors


def test_missing_parent_fails_closed():
    event = TraceEvent(
        event_id="event:decision:orphan",
        trace_id="trace:orphan",
        event_type="decision_recorded",
        occurred_at="2026-08-19T14:31:00Z",
        actor="nexus:control-plane",
        result="success",
        parent_event_id="event:not-present",
        decision_ref="decision:1",
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("parent_event_id must reference an event in the same trace" in error for error in result.errors)


def test_parent_cycle_is_rejected_once():
    first = TraceEvent(
        event_id="event:1",
        trace_id="trace:cycle",
        event_type="decision_recorded",
        occurred_at="2026-08-19T14:30:00Z",
        actor="nexus:control-plane",
        result="success",
        parent_event_id="event:2",
        decision_ref="decision:1",
    )
    second = TraceEvent(
        event_id="event:2",
        trace_id="trace:cycle",
        event_type="evaluation_completed",
        occurred_at="2026-08-19T14:31:00Z",
        actor="nexus:eval",
        result="success",
        parent_event_id="event:1",
        eval_ref="eval:1",
    )
    result = validate_trace((first, second))
    assert result.valid is False
    assert result.errors.count("trace parent links cannot contain a cycle") == 1
    assert "trace must contain exactly one root event" in result.errors


def test_duplicate_event_ids_are_rejected():
    event = _valid_chain()[0]
    result = validate_trace((event, event))
    assert result.valid is False
    assert "trace cannot contain duplicate event_id values" in result.errors


def test_event_specific_reference_requirements_fail_closed():
    event = TraceEvent(
        event_id="event:promotion:missing-ref",
        trace_id="trace:promotion:1",
        event_type="promotion_decided",
        occurred_at="2026-08-19T14:30:00Z",
        actor="nexus:promotion",
        result="blocked",
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("promotion_decided requires eval_ref" in error for error in result.errors)


def test_serialization_uses_stable_internal_names():
    event = _valid_chain()[2]
    serialized = event.to_dict()
    assert serialized["event_id"] == "event:eval:1"
    assert serialized["eval_ref"] == "eval:requirement-readiness:1"
    assert "span_id" not in serialized
    assert "otel" not in serialized
