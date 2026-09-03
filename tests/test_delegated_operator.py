from datetime import datetime, timedelta, timezone

from nexus_core.access_authority_registry import AccessState, ActionClass, ConnectorAccess
from nexus_core.delegated_operator import (
    AccessObservation,
    DelegatedWork,
    OperatorDisposition,
    route_delegated_work,
)


NOW = datetime(2026, 8, 28, 20, 20, tzinfo=timezone.utc)


def obs(connector: str, state: AccessState, *, age_hours: int = 0) -> AccessObservation:
    evidence = () if state in {AccessState.BLOCKED, AccessState.UNKNOWN} else ("live-probe",)
    return AccessObservation(
        ConnectorAccess(connector, state, evidence),
        NOW - timedelta(hours=age_hours),
        timedelta(hours=24),
    )


def work(action: ActionClass, *, connector: str = "gmail", reversible: bool = True) -> DelegatedWork:
    return DelegatedWork(
        work_id="w-1",
        project_id="PRJ-HYD-01",
        connector=connector,
        action_class=action,
        reversible=reversible,
        payload_digest="sha256:abc",
    )


def test_fresh_verified_read_can_execute_internally():
    result = route_delegated_work(work(ActionClass.READ), {"gmail": obs("gmail", AccessState.READ_VERIFIED)}, now=NOW)
    assert result.disposition is OperatorDisposition.EXECUTE_INTERNAL
    assert result.exact_approval_required is False


def test_fresh_verified_reversible_internal_write_can_execute_internally():
    result = route_delegated_work(
        work(ActionClass.INTERNAL_WRITE),
        {"gmail": obs("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.EXECUTE_INTERNAL


def test_irreversible_internal_write_is_rejected_before_connector_use():
    result = route_delegated_work(
        work(ActionClass.INTERNAL_WRITE, reversible=False),
        {"gmail": obs("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD
    assert any("reversible" in reason for reason in result.reasons)


def test_consequential_external_message_is_prepared_for_exact_approval_not_executed():
    result = route_delegated_work(
        work(ActionClass.EXTERNAL_COMMUNICATION),
        {"gmail": obs("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.PREPARE_APPROVAL
    assert result.exact_approval_required is True


def test_production_change_is_prepared_for_approval_even_with_write_verified_connector():
    result = route_delegated_work(
        work(ActionClass.PRODUCTION_CHANGE, connector="vercel"),
        {"vercel": obs("vercel", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.PREPARE_APPROVAL
    assert result.exact_approval_required is True


def test_stale_access_is_refreshed_before_any_authority_decision():
    result = route_delegated_work(
        work(ActionClass.READ),
        {"gmail": obs("gmail", AccessState.READ_VERIFIED, age_hours=25)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.REFRESH_ACCESS
    assert "stale" in result.reasons[0]


def test_missing_access_observation_requires_refresh():
    result = route_delegated_work(work(ActionClass.READ), {}, now=NOW)
    assert result.disposition is OperatorDisposition.REFRESH_ACCESS


def test_blocked_connector_stays_on_hold():
    result = route_delegated_work(
        work(ActionClass.READ, connector="apollo"),
        {"apollo": obs("apollo", AccessState.BLOCKED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD


def test_connector_binding_mismatch_fails_closed():
    result = route_delegated_work(
        work(ActionClass.READ, connector="gmail"),
        {"gmail": obs("drive", AccessState.READ_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD
    assert "binding mismatch" in result.reasons[0]


def test_naive_observation_time_fails_closed():
    observation = AccessObservation(
        ConnectorAccess("gmail", AccessState.READ_VERIFIED, ("probe",)),
        datetime(2026, 8, 28, 20, 0),
    )
    result = route_delegated_work(work(ActionClass.READ), {"gmail": observation}, now=NOW)
    assert result.disposition is OperatorDisposition.HOLD
    assert any("timezone-aware" in reason for reason in result.reasons)
