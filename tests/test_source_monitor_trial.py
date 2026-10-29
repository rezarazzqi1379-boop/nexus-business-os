from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from autonomy import AutonomyStore
from nexus_commercial_pilot import SOURCE
from nexus_router_runtime import PROJECT
from source_monitor_trial import TrialTransport, TrialMonitoringRuntime, UNGMConnector, trial_report

START = datetime(2026, 10, 29, tzinfo=timezone.utc)


def configured(path):
    store = AutonomyStore(path)
    store.configure_http_trial("trial", PROJECT, sources=("worldbank", "ungm"), starts_at=START)
    return store


def test_three_ticks_six_attempts_with_restart(tmp_path):
    path = tmp_path / "queue.db"
    for tick in range(3):
        store = configured(path)
        for source in ("worldbank", "ungm"):
            store.reserve_http_attempt("trial", PROJECT, tick=tick, source=source,
                                       now=START + timedelta(seconds=300*tick))
    assert len(store.http_trial_attempts("trial", PROJECT)) == 6
    with pytest.raises(PermissionError, match="budget_exhausted"):
        store.reserve_http_attempt("trial", PROJECT, tick=2, source="worldbank", now=START+timedelta(seconds=600))
    # These are reservations in a frozen clock, not six real requests.
    assert trial_report(store, "trial")["uncertain_attempts"] == 6


def test_concurrent_reservations_cannot_exceed_six(tmp_path):
    store = configured(tmp_path / "queue.db")
    def reserve(_):
        try:
            return store.reserve_http_attempt("trial", PROJECT, tick=0, source="worldbank", now=START)
        except PermissionError:
            return None
    with ThreadPoolExecutor(max_workers=10) as pool:
        assert sum(x is not None for x in pool.map(reserve, range(20))) == 6


def test_crash_after_commit_before_transport_never_refunds(tmp_path):
    path = tmp_path / "queue.db"
    store = configured(path)
    store.reserve_http_attempt("trial", PROJECT, tick=0, source="worldbank", now=START)
    restarted = configured(path)
    assert trial_report(restarted, "trial")["reserved_attempts"] == 1
    assert trial_report(restarted, "trial")["uncertain_attempts"] == 1


def test_failure_retry_and_budget_are_bound_to_transport(tmp_path):
    store = configured(tmp_path / "queue.db")
    calls = []
    def fail(url):
        calls.append(url)
        assert trial_report(store, "trial")["reserved_attempts"] == len(calls)
        raise RuntimeError("private-provider-response")
    transport = TrialTransport(store, trial_id="trial", tick=0, transport=fail, clock=lambda: START)
    for _ in range(6):
        with pytest.raises(RuntimeError, match="^bounded_trial_read_failed$"):
            transport(SOURCE)
    with pytest.raises(PermissionError):
        transport(SOURCE)
    assert len(calls) == 6
    assert trial_report(store, "trial")["transport_failures"] == 6
    assert "private-provider-response" not in str(trial_report(store, "trial"))


def test_crash_during_transport_preserves_unknown(tmp_path):
    store = configured(tmp_path / "queue.db")
    def crash(url):
        raise SystemExit()
    with pytest.raises(SystemExit):
        TrialTransport(store, trial_id="trial", tick=0, transport=crash, clock=lambda: START)(SOURCE)
    assert trial_report(store, "trial")["uncertain_attempts"] == 1


@pytest.mark.parametrize("tick,offset,source", [(3,900,"worldbank"),(0,-1,"worldbank"),
    (0,300,"worldbank"),(2,900,"worldbank"),(1,300,"other"),(True,0,"worldbank")])
def test_tick_window_and_source_bounds(tmp_path,tick,offset,source):
    store = configured(tmp_path / "queue.db")
    with pytest.raises((PermissionError,ValueError)):
        store.reserve_http_attempt("trial", PROJECT, tick=tick,source=source,now=START+timedelta(seconds=offset))
    assert not store.http_trial_attempts("trial", PROJECT)


def test_reconfiguration_cannot_reset_quota(tmp_path):
    store = configured(tmp_path / "queue.db")
    with pytest.raises(ValueError, match="immutable"):
        store.configure_http_trial("trial", PROJECT, sources=("worldbank","ungm"),starts_at=START+timedelta(days=1))
    with pytest.raises(PermissionError):
        store.reserve_http_attempt("trial","other",tick=0,source="worldbank",now=START)


def test_ungm_stays_blocked_and_no_transport_on_unknown_url(tmp_path):
    with pytest.raises(PermissionError, match="provider_permission"):
        UNGMConnector()("https://www.ungm.org/Public/Notice")
    store = configured(tmp_path / "queue.db")
    transport = TrialTransport(store,trial_id="trial",tick=0,transport=lambda _:pytest.fail("unexpected read"),clock=lambda:START)
    with pytest.raises(PermissionError):
        transport("https://other.invalid")
    assert not store.http_trial_attempts("trial",PROJECT)


def test_budgeted_existing_worker_and_supervisor(tmp_path):
    import json
    from source_monitor import tick
    current = datetime.now(timezone.utc)
    path = tmp_path / "queue.db"
    store = AutonomyStore(path)
    store.configure_http_trial("trial",PROJECT,sources=("worldbank","ungm"),starts_at=current)
    fixture = json.dumps(dict(rows="0",os="0",page="1",total="0",procnotices=[])).encode()
    runtime = TrialMonitoringRuntime(path,trial_id="trial",tick=0,transport=lambda _:fixture)
    result = tick(runtime,now=current.isoformat())
    assert result["status"] == "ACCEPTED"
    assert result["source_mode"] == "FROZEN_TEST_FIXTURE"
    assert trial_report(store,"trial")["reserved_attempts"] == 1
    assert store.http_trial_attempts("trial",PROJECT)[0]["outcome"] == "RESPONSE_RECEIVED"
    tick(runtime,now=current.isoformat())
    assert trial_report(store,"trial")["reserved_attempts"] == 1
