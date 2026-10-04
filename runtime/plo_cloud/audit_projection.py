from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ProjectedAuditEvent:
    """PR #10-compatible metadata projection from PLO runtime events.

    This is deliberately a projection, not the canonical AuditEvent authority.
    It carries only compact metadata and never turns PLO-native approval rows into
    canonical human-gate decisions.
    """

    event_id: str
    trace_id: str
    event_type: str
    occurred_at: str
    actor_type: str
    subject_ref: str
    result_class: str
    privacy_mode: str = "metadata_only"
    action_ref: str = ""
    correlation_refs: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


class AuditProjectionError(ValueError):
    pass


def _require_compact(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AuditProjectionError(f"{name} must be compact non-empty text")
    if len(value) > 256 or any(ord(ch) < 32 for ch in value):
        raise AuditProjectionError(f"{name} is invalid")
    return value


def project_runtime_audit(*, audit_id: int, ts: str, action: str, run_id: str, result: str | None, binding_digest: str | None) -> ProjectedAuditEvent | None:
    """Project only semantics that are safe to express under PR #10.

    Runtime-local enqueue and native approval decisions remain intentionally
    unprojected until their canonical owners are consolidated. This prevents PLO
    from becoming a second approval/audit authority.
    """

    if not isinstance(audit_id, int) or audit_id <= 0:
        raise AuditProjectionError("audit_id must be a positive integer")
    ts = _require_compact("ts", ts)
    try:
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError as exc:
        raise AuditProjectionError("ts must be ISO-8601") from exc
    if parsed.tzinfo is None:
        raise AuditProjectionError("ts must include timezone")
    action = _require_compact("action", action)
    run_id = _require_compact("run_id", run_id)

    if action == "read_only_completed":
        digest = _require_compact("binding_digest", binding_digest)
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise AuditProjectionError("binding_digest must be lowercase SHA-256 hex")
        result_ref = _require_compact("result", result)
        return ProjectedAuditEvent(
            event_id=f"plo-audit:{audit_id}",
            trace_id=f"plo-run:{run_id}",
            event_type="action_attempted",
            occurred_at=ts,
            actor_type="system",
            subject_ref=f"plo-run:{run_id}",
            result_class="passed",
            action_ref=f"sha256:{digest}",
            correlation_refs=(result_ref,),
            tags=("plo", "read_only", "shadow"),
        )

    if action == "orphan_recovered":
        recovery = _require_compact("result", result)
        result_class = "blocked" if recovery in {"reconciliation_required", "retry_budget_exhausted"} else "unknown"
        return ProjectedAuditEvent(
            event_id=f"plo-audit:{audit_id}",
            trace_id=f"plo-run:{run_id}",
            event_type="decision_recorded",
            occurred_at=ts,
            actor_type="system",
            subject_ref=f"plo-run:{run_id}",
            result_class=result_class,
            correlation_refs=(f"plo-recovery:{recovery}",),
            tags=("plo", "recovery"),
        )

    # enqueue / operation_authorized / other runtime-internal events are not
    # silently promoted into PR #10 canonical semantics.
    return None
