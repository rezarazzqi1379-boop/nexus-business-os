from datetime import datetime, timezone

import pytest

from nexus_core.causal_trace import TraceContext, TraceSpan, child_context, validate_span


def ctx(**overrides):
    base = dict(
        trace_id="trace-1",
        span_id="span-1",
        parent_span_id=None,
        goal_ref="goal-commercial",
        project_ref="hydrotester",
        source_refs=("gmail:thread-1",),
        started_at=datetime(2026, 8, 19, 20, 0, tzinfo=timezone.utc),
    )
    base.update(overrides)
    return TraceContext(**base)


def test_terminal_span_requires_end_time():
    span = TraceSpan(context=ctx(), operation="qualify_counterparty", status="ok", ended_at=None)
    assert "terminal_span_missing_end" in validate_span(span)


def test_child_preserves_trace_and_scope():
    parent = ctx()
    child = child_context(
        parent,
        span_id="span-2",
        source_refs=("hubspot:company-1",),
        started_at=datetime(2026, 8, 19, 20, 1, tzinfo=timezone.utc),
    )
    assert child.trace_id == parent.trace_id
    assert child.parent_span_id == parent.span_id
    assert child.goal_ref == parent.goal_ref
    assert child.project_ref == parent.project_ref


def test_child_rejects_self_parent_span():
    with pytest.raises(ValueError):
        child_context(
            ctx(),
            span_id="span-1",
            source_refs=("source:2",),
            started_at=datetime(2026, 8, 19, 20, 1, tzinfo=timezone.utc),
        )


def test_ended_before_started_fails_closed():
    span = TraceSpan(
        context=ctx(),
        operation="request_quote",
        status="error",
        ended_at=datetime(2026, 8, 19, 19, 59, tzinfo=timezone.utc),
    )
    assert "ended_before_started" in validate_span(span)
