from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from nexus_core.access_authority_registry import AccessState, ConnectorAccess
from nexus_core.autonomy_adapter import delegated_work_from_claim, route_claimed_work
from nexus_core.delegated_operator import AccessObservation, OperatorDisposition


NOW = datetime(2026, 8, 29, 5, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class Claim:
    work_id: str = "q-1"
    project: str = "PRJ-HYD-01"
    action: str = "connector_work"
    payload: dict | None = None
    attempt: int = 1
    lease_until: str = "2026-08-29T05:01:00+00:00"


def claim(**overrides) -> Claim:
    payload = {
        "project_id": "PRJ-HYD-01",
        "connector": "gmail",
        "action_class": "READ",
        "reversible": True,
        "payload_digest": "sha256:abc",
    }
    payload.update(overrides.pop("payload_overrides", {}))
    return Claim(payload=payload, **overrides)


def observation(connector: str, state: AccessState, *, age_hours: int = 0) -> AccessObservation:
    evidence = () if state in {AccessState.BLOCKED, AccessState.UNKNOWN} else ("live-probe",)
    return AccessObservation(
        ConnectorAccess(connector, state, evidence),
        NOW - timedelta(hours=age_hours),
        timedelta(hours=24),
    )


def test_queue_read_with_fresh_access_can_enter_internal_execution_lane():
    result = route_claimed_work(
        claim(),
        {"gmail": observation("gmail", AccessState.READ_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.EXECUTE_INTERNAL
    assert result.worker_may_complete is True


def test_queue_external_message_never_becomes_completable_from_write_capability():
    result = route_claimed_work(
        claim(payload_overrides={"action_class": "EXTERNAL_COMMUNICATION"}),
        {"gmail": observation("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.PREPARE_APPROVAL
    assert result.exact_approval_required is True
    assert result.worker_may_complete is False


def test_stale_connector_claim_cannot_be_completed():
    result = route_claimed_work(
        claim(),
        {"gmail": observation("gmail", AccessState.READ_VERIFIED, age_hours=25)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.REFRESH_ACCESS
    assert result.worker_may_complete is False


def test_blocked_connector_claim_cannot_be_completed():
    result = route_claimed_work(
        claim(payload_overrides={"connector": "apollo"}),
        {"apollo": observation("apollo", AccessState.BLOCKED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD
    assert result.worker_may_complete is False


def test_payload_cannot_move_claim_across_projects():
    result = route_claimed_work(
        claim(payload_overrides={"project_id": "PRJ-CAN-01"}),
        {"gmail": observation("gmail", AccessState.READ_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD
    assert "project binding mismatch" in result.reasons[0]
    assert result.worker_may_complete is False


def test_unknown_action_class_fails_closed():
    result = route_claimed_work(
        claim(payload_overrides={"action_class": "SEND_ANYTHING"}),
        {"gmail": observation("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD
    assert "unknown action_class" in result.reasons[0]


def test_internal_write_requires_explicit_boolean_reversibility():
    result = route_claimed_work(
        claim(payload_overrides={"action_class": "INTERNAL_WRITE", "reversible": "true"}),
        {"gmail": observation("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert result.disposition is OperatorDisposition.HOLD
    assert "reversible boolean required" in result.reasons[0]


def test_adapter_does_not_trust_claim_action_string_as_authority():
    suspicious = claim(action="send_email")
    delegated = delegated_work_from_claim(suspicious)
    assert delegated.action_class.value == "READ"
    assert delegated.connector == "gmail"
