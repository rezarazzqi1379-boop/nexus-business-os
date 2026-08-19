from nexus_core.trace import TraceEvent, validate_trace


def _valid_chain():
    return (
        TraceEvent(
            event_id="event:evidence:1",
            trace_id="trace:hydrotester:1",
            event_type="evidence_observed",
            occurred_at="2026-08-19T14:30:00Z",
            subject_ref="hydrotester:rfq:1",
            result_class="observed",
            evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
            data_classification="confidential",
        ),
        TraceEvent(
            event_id="event:decision:1",
            trace_id="trace:hydrotester:1",
            event_type="decision_recorded",
            occurred_at="2026-08-19T14:31:00Z",
            subject_ref="hydrotester:rfq:1",
            result_class="accepted",
            evidence_refs=("gmail:message:1a018c1b2c80c8e3",),
            parent_event_id="event:evidence:1",
            decision_ref="decision:requirement-readiness:1",
            data_classification="confidential",
        ),
        TraceEvent(
            event_id="event:eval:1",
            trace_id="trace:hydrotester:1",
            event_type="evaluation_completed",
            occurred_at="2026-08-19T14:32:00Z",
            subject_ref="hydrotester:rfq:1",
            result_class="failed",
            evidence_refs=("github:pr:2",),
            parent_event_id="event:decision:1",
            eval_ref="eval:requirement-readiness:1",
            data_classification="internal",
        ),
        TraceEvent(
            event_id="event:promotion:1",
            trace_id="trace:hydrotester:1",
            event_type="promotion_decided",
            occurred_at="2026-08-19T14:33:00Z",
            subject_ref="hydrotester:rfq:1",
            result_class="blocked",
            evidence_refs=("github:pr:6",),
            parent_event_id="event:eval:1",
            eval_ref="promotion:requirement-readiness:1",
            data_classification="internal",
        ),
        TraceEvent(
            event_id="event:gate:1",
            trace_id="trace:hydrotester:1",
            event_type="human_gate_evaluated",
            occurred_at="2026-08-19T14:34:00Z",
            subject_ref="hydrotester:rfq:1",
            result_class="blocked",
            evidence_refs=("github:pr:4",),
            parent_event_id="event:promotion:1",
            action_ref="send:hydrotester-final-rfq:1",
            data_classification="internal",
        ),
    )


def test_valid_trace_reconstructs_single_chain_without_payloads():
    result = validate_trace(_valid_chain())
    assert result.valid is True
    assert result.errors == ()
    assert result.root_event_ids == ("event:evidence:1",)
    assert result.terminal_event_ids == ("event:gate:1",)


def test_sensitive_payload_is_rejected_even_when_reference_exists():
    event = TraceEvent(
        event_id="event:evidence:secret",
        trace_id="trace:secret:1",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:30:00Z",
        subject_ref="supplier:commercial-email",
        result_class="observed",
        evidence_refs=("gmail:message:secret",),
        payload_ref="gmail:message:secret",
        data_classification="restricted",
        sensitive_payload_included=True,
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("sensitive payloads are forbidden" in error for error in result.errors)


def test_cross_trace_parent_reference_is_rejected():
    first = TraceEvent(
        event_id="event:1",
        trace_id="trace:1",
        event_type="evidence_observed",
        occurred_at="2026-08-19T14:30:00Z",
        subject_ref="subject:1",
        result_class="observed",
        evidence_refs=("evidence:1",),
    )
    second = TraceEvent(
        event_id="event:2",
        trace_id="trace:2",
        event_type="decision_recorded",
        occurred_at="2026-08-19T14:31:00Z",
        subject_ref="subject:1",
        result_class="accepted",
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
        subject_ref="subject:1",
        result_class="accepted",
        parent_event_id="event:not-present",
        decision_ref="decision:1",
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("parent_event_id must reference an event in the same trace" in error for error in result.errors)


def test_parent_cycle_is_rejected():
    first = TraceEvent(
        event_id="event:1",
        trace_id="trace:cycle",
        event_type="decision_recorded",
        occurred_at="2026-08-19T14:30:00Z",
        subject_ref="subject:1",
        result_class="accepted",
        parent_event_id="event:2",
        decision_ref="decision:1",
    )
    second = TraceEvent(
        event_id="event:2",
        trace_id="trace:cycle",
        event_type="evaluation_completed",
        occurred_at="2026-08-19T14:31:00Z",
        subject_ref="subject:1",
        result_class="passed",
        parent_event_id="event:1",
        eval_ref="eval:1",
    )
    result = validate_trace((first, second))
    assert result.valid is False
    assert "trace parent links cannot contain a cycle" in result.errors
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
        subject_ref="subject:1",
        result_class="blocked",
    )
    result = validate_trace((event,))
    assert result.valid is False
    assert any("promotion_decided requires eval_ref" in error for error in result.errors)
