from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from nexus_core.worker_lifecycle import SettlementDisposition, SettlementPlan


class SettlementStore(Protocol):
    def complete(self, work_id: str, worker_id: str) -> None: ...
    def fail(self, work_id: str, worker_id: str, error: str, *, now: datetime | None = None) -> str: ...
    def defer(
        self,
        work_id: str,
        worker_id: str,
        reason: str,
        *,
        delay_seconds: int = 60,
        now: datetime | None = None,
    ) -> str: ...


@dataclass(frozen=True)
class SettlementResult:
    durable_action: str
    durable_status: str | None
    mutated: bool


def _reason(plan: SettlementPlan) -> str:
    return "; ".join(plan.reasons)[:500] or plan.disposition.value


def apply_settlement(
    store: SettlementStore,
    work_id: str,
    worker_id: str,
    plan: SettlementPlan,
    *,
    now: datetime | None = None,
    access_refresh_delay_seconds: int = 60,
    approval_poll_delay_seconds: int = 300,
) -> SettlementResult:
    """Persist one already-planned worker settlement without expanding authority.

    COMPLETE is allowed only when the planner explicitly permits completion. Execution failures
    consume the existing retry budget via ``fail``. Approval/access waits use ``defer`` so they
    release the lease without consuming execution retry budget. HOLD is deliberately non-mutating:
    ambiguous/manual-review work must not be silently requeued, completed or converted to failure.
    """
    if not work_id.strip() or not worker_id.strip():
        raise ValueError("work_id and worker_id required")

    if plan.disposition is SettlementDisposition.COMPLETE:
        if not plan.may_mark_complete:
            raise PermissionError("completion_not_authorized_by_settlement_plan")
        store.complete(work_id, worker_id)
        return SettlementResult("complete", "completed", True)

    if plan.disposition is SettlementDisposition.RETRY_EXECUTION:
        status = store.fail(work_id, worker_id, _reason(plan), now=now)
        return SettlementResult("fail", status, True)

    if plan.disposition is SettlementDisposition.WAIT_ACCESS_REFRESH:
        status = store.defer(
            work_id,
            worker_id,
            f"access_refresh:{_reason(plan)}",
            delay_seconds=access_refresh_delay_seconds,
            now=now,
        )
        return SettlementResult("defer_access", status, True)

    if plan.disposition is SettlementDisposition.WAIT_EXACT_APPROVAL:
        status = store.defer(
            work_id,
            worker_id,
            f"exact_approval:{_reason(plan)}",
            delay_seconds=approval_poll_delay_seconds,
            now=now,
        )
        return SettlementResult("defer_approval", status, True)

    if plan.disposition is SettlementDisposition.HOLD:
        return SettlementResult("hold_manual", None, False)

    raise ValueError("unknown_settlement_disposition")
