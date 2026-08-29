from datetime import datetime, timedelta, timezone

from autonomy import AutonomyStore, WorkItem
from nexus_core.access_authority_registry import AccessState, ConnectorAccess
from nexus_core.autonomy_adapter import route_claimed_work
from nexus_core.delegated_operator import AccessObservation, OperatorDisposition


NOW = datetime(2026, 8, 29, 5, 30, tzinfo=timezone.utc)


def payload(action_class: str = "READ", *, connector: str = "gmail") -> dict:
    return {
        "project_id": "PRJ-HYD-01",
        "connector": connector,
        "action_class": action_class,
        "reversible": True,
        "payload_digest": "sha256:queue-proof",
    }


def obs(connector: str, state: AccessState, *, age_hours: int = 0) -> AccessObservation:
    evidence = () if state in {AccessState.BLOCKED, AccessState.UNKNOWN} else ("live-probe",)
    return AccessObservation(
        ConnectorAccess(connector, state, evidence),
        NOW - timedelta(hours=age_hours),
        timedelta(hours=24),
    )


def test_real_queue_claim_can_route_to_internal_lane_without_auto_completing(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(WorkItem("w-read", "PRJ-HYD-01", "connector_work", payload()), now=NOW)
    claimed = store.claim_next("worker-1", now=NOW)
    assert claimed is not None

    routed = route_claimed_work(
        claimed,
        {"gmail": obs("gmail", AccessState.READ_VERIFIED)},
        now=NOW,
    )
    assert routed.disposition is OperatorDisposition.EXECUTE_INTERNAL
    assert routed.worker_may_complete is True

    # Routing alone must not mutate durable queue completion state.
    second_worker = store.claim_next("worker-2", now=NOW + timedelta(seconds=61))
    assert second_worker is not None
    assert second_worker.work_id == "w-read"


def test_real_queue_external_action_waits_for_approval_and_is_not_completed(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(
        WorkItem("w-send", "PRJ-HYD-01", "connector_work", payload("EXTERNAL_COMMUNICATION")),
        now=NOW,
    )
    claimed = store.claim_next("worker-1", now=NOW)
    assert claimed is not None

    routed = route_claimed_work(
        claimed,
        {"gmail": obs("gmail", AccessState.WRITE_VERIFIED)},
        now=NOW,
    )
    assert routed.disposition is OperatorDisposition.PREPARE_APPROVAL
    assert routed.exact_approval_required is True
    assert routed.worker_may_complete is False

    # Existing lease/retry semantics remain intact; no adapter-side completion occurs.
    reclaimed = store.claim_next("worker-2", now=NOW + timedelta(seconds=61))
    assert reclaimed is not None
    assert reclaimed.work_id == "w-send"


def test_real_queue_stale_access_cannot_enter_execution_lane(tmp_path):
    store = AutonomyStore(tmp_path / "autonomy.db")
    assert store.enqueue(WorkItem("w-stale", "PRJ-HYD-01", "connector_work", payload()), now=NOW)
    claimed = store.claim_next("worker-1", now=NOW)
    assert claimed is not None

    routed = route_claimed_work(
        claimed,
        {"gmail": obs("gmail", AccessState.READ_VERIFIED, age_hours=25)},
        now=NOW,
    )
    assert routed.disposition is OperatorDisposition.REFRESH_ACCESS
    assert routed.worker_may_complete is False
