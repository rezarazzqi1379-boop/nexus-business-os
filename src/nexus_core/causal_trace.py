from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


@dataclass(frozen=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    goal_ref: str | None
    project_ref: str | None
    source_refs: tuple[str, ...]
    started_at: datetime


@dataclass(frozen=True)
class TraceSpan:
    context: TraceContext
    operation: str
    status: str
    ended_at: datetime | None = None


def _unique_non_empty(values: Iterable[str]) -> bool:
    items = tuple(values)
    return all(isinstance(v, str) and v.strip() for v in items) and len(items) == len(set(items))


def validate_trace_context(ctx: TraceContext) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(ctx.trace_id, str) or not ctx.trace_id.strip():
        errors.append("invalid_trace_id")
    if not isinstance(ctx.span_id, str) or not ctx.span_id.strip():
        errors.append("invalid_span_id")
    if ctx.parent_span_id is not None and (not isinstance(ctx.parent_span_id, str) or not ctx.parent_span_id.strip()):
        errors.append("invalid_parent_span_id")
    if ctx.parent_span_id == ctx.span_id:
        errors.append("self_parent_span")
    if ctx.started_at.tzinfo is None:
        errors.append("timezone_naive_started_at")
    if not _unique_non_empty(ctx.source_refs):
        errors.append("invalid_source_refs")
    if ctx.goal_ref is None and ctx.project_ref is None:
        errors.append("missing_business_or_goal_scope")
    return tuple(errors)


def validate_span(span: TraceSpan) -> tuple[str, ...]:
    errors = list(validate_trace_context(span.context))
    if not isinstance(span.operation, str) or not span.operation.strip():
        errors.append("invalid_operation")
    if span.status not in {"started", "ok", "error", "blocked", "human_gate"}:
        errors.append("invalid_status")
    if span.ended_at is not None:
        if span.ended_at.tzinfo is None:
            errors.append("timezone_naive_ended_at")
        elif span.ended_at < span.context.started_at:
            errors.append("ended_before_started")
    if span.status in {"ok", "error", "blocked", "human_gate"} and span.ended_at is None:
        errors.append("terminal_span_missing_end")
    return tuple(errors)


def child_context(parent: TraceContext, *, span_id: str, source_refs: tuple[str, ...], started_at: datetime) -> TraceContext:
    """Create a causally-linked child context without inventing a new business scope."""
    child = TraceContext(
        trace_id=parent.trace_id,
        span_id=span_id,
        parent_span_id=parent.span_id,
        goal_ref=parent.goal_ref,
        project_ref=parent.project_ref,
        source_refs=source_refs,
        started_at=started_at,
    )
    errors = validate_trace_context(child)
    if errors:
        raise ValueError(",".join(errors))
    return child
