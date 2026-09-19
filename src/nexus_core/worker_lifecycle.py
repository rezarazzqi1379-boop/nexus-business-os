from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from nexus_core.autonomy_adapter import QueueRoute
from nexus_core.delegated_operator import OperatorDisposition


class SettlementDisposition(str, Enum):
    COMPLETE = "COMPLETE"
    RETRY_EXECUTION = "RETRY_EXECUTION"
    WAIT_ACCESS_REFRESH = "WAIT_ACCESS_REFRESH"
    WAIT_EXACT_APPROVAL = "WAIT_EXACT_APPROVAL"
    HOLD = "HOLD"


@dataclass(frozen=True)
class SettlementPlan:
    disposition: SettlementDisposition
    may_mark_complete: bool
    consume_execution_attempt: bool
    reasons: tuple[str, ...]


def plan_settlement(route: QueueRoute, *, operation_succeeded: bool | None = None) -> SettlementPlan:
    """Translate a governed queue route into a durable worker lifecycle intent.

    This function is deliberately side-effect free. It prevents routing success from being
    mistaken for execution success. Only a completed internal operation may be marked complete.
    Approval/access waits are not execution failures and therefore must not consume a retry attempt
    when a persistence adapter is added.
    """
    if route.disposition is OperatorDisposition.EXECUTE_INTERNAL:
        if operation_succeeded is True:
            return SettlementPlan(
                SettlementDisposition.COMPLETE,
                True,
                True,
                ("internal operation completed successfully",),
            )
        if operation_succeeded is False:
            return SettlementPlan(
                SettlementDisposition.RETRY_EXECUTION,
                False,
                True,
                ("internal operation failed after entering execution lane",),
            )
        return SettlementPlan(
            SettlementDisposition.HOLD,
            False,
            False,
            ("execution outcome required before completion",),
        )

    if operation_succeeded is True:
        return SettlementPlan(
            SettlementDisposition.HOLD,
            False,
            False,
            ("non-execution route cannot accept a success outcome",),
        )

    if route.disposition is OperatorDisposition.REFRESH_ACCESS:
        return SettlementPlan(
            SettlementDisposition.WAIT_ACCESS_REFRESH,
            False,
            False,
            route.reasons or ("refresh live connector access before execution",),
        )
    if route.disposition is OperatorDisposition.PREPARE_APPROVAL:
        return SettlementPlan(
            SettlementDisposition.WAIT_EXACT_APPROVAL,
            False,
            False,
            route.reasons or ("exact approval required before consequential execution",),
        )
    return SettlementPlan(
        SettlementDisposition.HOLD,
        False,
        False,
        route.reasons or ("work remains held",),
    )
