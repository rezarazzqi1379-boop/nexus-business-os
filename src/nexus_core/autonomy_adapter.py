from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Protocol, Any

from nexus_core.access_authority_registry import ActionClass
from nexus_core.delegated_operator import (
    AccessObservation,
    DelegatedWork,
    OperatorDecision,
    OperatorDisposition,
    route_delegated_work,
)


class ClaimedWorkLike(Protocol):
    work_id: str
    project: str
    action: str
    payload: dict
    attempt: int
    lease_until: str


@dataclass(frozen=True)
class QueueRoute:
    work_id: str
    disposition: OperatorDisposition
    exact_approval_required: bool
    reasons: tuple[str, ...]
    worker_may_complete: bool


def _payload_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} required")
    return value.strip()


def delegated_work_from_claim(claimed: ClaimedWorkLike) -> DelegatedWork:
    """Translate a leased AutonomyStore claim into the governed routing contract.

    The durable queue remains authoritative for lease/retry state. The payload may describe
    requested connector work, but cannot grant authority or override the claim's project binding.
    """
    if not isinstance(claimed.payload, dict):
        raise ValueError("payload must be an object")

    payload_project = claimed.payload.get("project_id")
    if payload_project is not None and payload_project != claimed.project:
        raise ValueError("payload project binding mismatch")

    connector = _payload_string(claimed.payload, "connector")
    action_text = _payload_string(claimed.payload, "action_class")
    payload_digest = _payload_string(claimed.payload, "payload_digest")

    try:
        action_class = ActionClass(action_text)
    except ValueError as exc:
        raise ValueError("unknown action_class") from exc

    reversible = claimed.payload.get("reversible")
    if not isinstance(reversible, bool):
        raise ValueError("reversible boolean required")

    return DelegatedWork(
        work_id=claimed.work_id,
        project_id=claimed.project,
        connector=connector,
        action_class=action_class,
        reversible=reversible,
        payload_digest=payload_digest,
    )


def route_claimed_work(
    claimed: ClaimedWorkLike,
    observations: Mapping[str, AccessObservation],
    *,
    now: datetime | None = None,
) -> QueueRoute:
    """Route one already-leased queue item without mutating queue state.

    Only EXECUTE_INTERNAL is eligible for worker completion after the actual internal operation
    succeeds. REFRESH_ACCESS, PREPARE_APPROVAL and HOLD must remain incomplete so the caller can
    refresh, prepare approval, or fail/requeue using the existing AutonomyStore semantics.
    """
    try:
        delegated = delegated_work_from_claim(claimed)
    except ValueError as exc:
        return QueueRoute(
            work_id=getattr(claimed, "work_id", ""),
            disposition=OperatorDisposition.HOLD,
            exact_approval_required=False,
            reasons=(str(exc),),
            worker_may_complete=False,
        )

    decision: OperatorDecision = route_delegated_work(delegated, observations, now=now)
    may_complete = decision.disposition is OperatorDisposition.EXECUTE_INTERNAL
    return QueueRoute(
        work_id=claimed.work_id,
        disposition=decision.disposition,
        exact_approval_required=decision.exact_approval_required,
        reasons=decision.reasons,
        worker_may_complete=may_complete,
    )
