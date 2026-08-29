from nexus_core.autonomy_adapter import QueueRoute
from nexus_core.delegated_operator import OperatorDisposition
from nexus_core.worker_lifecycle import SettlementDisposition, plan_settlement


def route(disposition: OperatorDisposition, *, may_complete: bool = False, approval: bool = False) -> QueueRoute:
    return QueueRoute(
        work_id="w-1",
        disposition=disposition,
        exact_approval_required=approval,
        reasons=("reason",),
        worker_may_complete=may_complete,
    )


def test_routing_to_internal_lane_is_not_enough_to_complete():
    result = plan_settlement(route(OperatorDisposition.EXECUTE_INTERNAL, may_complete=True))
    assert result.disposition is SettlementDisposition.HOLD
    assert result.may_mark_complete is False
    assert result.consume_execution_attempt is False


def test_only_successful_internal_operation_may_complete():
    result = plan_settlement(
        route(OperatorDisposition.EXECUTE_INTERNAL, may_complete=True),
        operation_succeeded=True,
    )
    assert result.disposition is SettlementDisposition.COMPLETE
    assert result.may_mark_complete is True
    assert result.consume_execution_attempt is True


def test_failed_internal_operation_routes_to_retry_and_consumes_attempt():
    result = plan_settlement(
        route(OperatorDisposition.EXECUTE_INTERNAL, may_complete=True),
        operation_succeeded=False,
    )
    assert result.disposition is SettlementDisposition.RETRY_EXECUTION
    assert result.may_mark_complete is False
    assert result.consume_execution_attempt is True


def test_approval_wait_never_counts_as_execution_failure():
    result = plan_settlement(
        route(OperatorDisposition.PREPARE_APPROVAL, approval=True),
        operation_succeeded=None,
    )
    assert result.disposition is SettlementDisposition.WAIT_EXACT_APPROVAL
    assert result.may_mark_complete is False
    assert result.consume_execution_attempt is False


def test_access_refresh_wait_never_counts_as_execution_failure():
    result = plan_settlement(route(OperatorDisposition.REFRESH_ACCESS))
    assert result.disposition is SettlementDisposition.WAIT_ACCESS_REFRESH
    assert result.consume_execution_attempt is False


def test_hold_never_completes():
    result = plan_settlement(route(OperatorDisposition.HOLD))
    assert result.disposition is SettlementDisposition.HOLD
    assert result.may_mark_complete is False
    assert result.consume_execution_attempt is False


def test_success_outcome_cannot_be_injected_into_non_execution_route():
    result = plan_settlement(
        route(OperatorDisposition.PREPARE_APPROVAL, approval=True),
        operation_succeeded=True,
    )
    assert result.disposition is SettlementDisposition.HOLD
    assert result.may_mark_complete is False
