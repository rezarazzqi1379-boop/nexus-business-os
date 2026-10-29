from concurrent.futures import ThreadPoolExecutor
import sqlite3

import pytest

from nexus_http_attempt_budget import AttemptBudget, AttemptBudgetExceeded


def test_three_ticks_six_attempts_across_restart(tmp_path):
    path = tmp_path / "budget.db"
    reads = []
    for tick in range(3):
        budget = AttemptBudget(path, scope="PRJ-NEXUS-SANDBOX:worldbank:trial", max_attempts=6)
        for _ in range(2):
            assert budget.read(str(tick), lambda url: reads.append(url) or b"ok",
                               "https://example.org/") == b"ok"
    assert len(reads) == 6
    with pytest.raises(AttemptBudgetExceeded):
        AttemptBudget(path, scope="PRJ-NEXUS-SANDBOX:worldbank:trial").read(
            "3", lambda url: pytest.fail("HTTP must not happen"), "https://example.org/")


def test_failure_consumes_slot_and_restart_does_not_refund(tmp_path):
    path = tmp_path / "budget.db"
    budget = AttemptBudget(path, scope="trial", max_attempts=1)
    def broken(_):
        raise OSError("network failure")
    with pytest.raises(OSError):
        budget.read("tick0", broken, "https://example.org/")
    assert AttemptBudget(path, scope="trial", max_attempts=1).count() == 1
    with pytest.raises(AttemptBudgetExceeded):
        AttemptBudget(path, scope="trial", max_attempts=1).reserve("tick0-retry")


def test_concurrent_reservations_never_exceed_cap(tmp_path):
    path = tmp_path / "budget.db"
    AttemptBudget(path, scope="trial")
    def attempt(i):
        try:
            AttemptBudget(path, scope="trial").reserve(str(i))
            return True
        except AttemptBudgetExceeded:
            return False
    with ThreadPoolExecutor(max_workers=12) as pool:
        results = list(pool.map(attempt, range(30)))
    assert sum(results) == 6
    assert AttemptBudget(path, scope="trial").count() == 6


def test_scope_and_cap_cannot_be_widened(tmp_path):
    path = tmp_path / "budget.db"
    AttemptBudget(path, scope="trial", max_attempts=3)
    with pytest.raises(ValueError, match="immutable"):
        AttemptBudget(path, scope="trial", max_attempts=6)
    with pytest.raises(ValueError):
        AttemptBudget(path, scope="invalid scope")
    with pytest.raises(ValueError):
        AttemptBudget(path, scope="trial", max_attempts=7)


def test_reservation_is_committed_before_transport(tmp_path):
    path = tmp_path / "budget.db"
    budget = AttemptBudget(path, scope="trial", max_attempts=1)
    def transport(_):
        assert AttemptBudget(path, scope="trial", max_attempts=1).count() == 1
        return b"response"
    assert budget.read("tick", transport, "https://example.org/") == b"response"


def test_guarded_transport_is_fail_closed(tmp_path):
    from nexus_http_attempt_budget import budgeted_transport
    budget = AttemptBudget(tmp_path / "budget.db", scope="trial", max_attempts=1)
    calls = []
    transport = budgeted_transport(budget, tick_id="tick0",
                                   transport=lambda url: calls.append(url) or b"ok")
    assert transport("https://example.org/") == b"ok"
    with pytest.raises(AttemptBudgetExceeded):
        transport("https://example.org/")
    assert len(calls) == 1


def test_guarded_transport_rejects_non_callable(tmp_path):
    from nexus_http_attempt_budget import budgeted_transport
    budget = AttemptBudget(tmp_path / "budget.db", scope="trial")
    with pytest.raises(TypeError):
        budgeted_transport(budget, tick_id="tick0", transport=None)


def test_monitor_execution_reserves_before_fixture_transport(tmp_path):
    import json
    from datetime import datetime, timezone
    from hashlib import sha256
    from source_monitor import MonitoringRuntime, tick
    from nexus_commercial_pilot import SOURCE
    body = json.dumps({"rows": "0", "total": "0", "os": "0", "page": "1",
                       "procnotices": []}).encode()
    budget = AttemptBudget(tmp_path / "budget.db", scope="monitor:trial", max_attempts=1)
    seen = []
    def transport(url):
        assert url == SOURCE
        assert budget.count() == 1
        seen.append(url)
        return body
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=transport, attempt_budget=budget)
    result = tick(runtime, now=datetime.now(timezone.utc).isoformat(), interval_seconds=86400)
    assert result["supervisor"] == "accepted"
    assert len(seen) == 1
    assert budget.count() == 1
    with pytest.raises(PermissionError):
        runtime.transport(SOURCE)


def test_monitor_replay_does_not_consume_extra_budget(tmp_path):
    import json
    from datetime import datetime, timezone
    from source_monitor import MonitoringRuntime, tick
    body = json.dumps({"rows": "0", "total": "0", "os": "0", "page": "1",
                       "procnotices": []}).encode()
    budget = AttemptBudget(tmp_path / "budget.db", scope="monitor:replay", max_attempts=1)
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: body,
                                attempt_budget=budget)
    now = datetime.now(timezone.utc).isoformat()
    tick(runtime, now=now, interval_seconds=86400)
    tick(runtime, now=now, interval_seconds=86400)
    assert budget.count() == 1


def test_live_mode_always_installs_durable_budget(tmp_path):
    from source_monitor import MonitoringRuntime
    runtime = MonitoringRuntime(tmp_path / "queue.db")
    assert runtime.source_mode == "REAL_PUBLIC_HTTP"
    assert isinstance(runtime.attempt_budget, AttemptBudget)
    assert runtime.attempt_budget.max_attempts == 6
    assert runtime.attempt_budget.count() == 0
    with pytest.raises(PermissionError, match="task_context"):
        runtime.transport("https://example.org/not-allowlisted")
    assert runtime.attempt_budget.count() == 0


def test_live_budget_persists_on_runtime_restart(tmp_path):
    from source_monitor import MonitoringRuntime
    path = tmp_path / "queue.db"
    first = MonitoringRuntime(path)
    first.attempt_budget.reserve("tick-1")
    second = MonitoringRuntime(path)
    assert second.attempt_budget.count() == 1
    assert second.attempt_budget.scope == first.attempt_budget.scope


def test_live_mode_rejects_alternate_budget_scope_or_cap(tmp_path):
    from source_monitor import MonitoringRuntime
    path = tmp_path / "queue.db"
    rogue = AttemptBudget(tmp_path / "other.db", scope="other", max_attempts=1)
    with pytest.raises(ValueError, match="binding_mismatch"):
        MonitoringRuntime(path, attempt_budget=rogue)


def test_live_mode_rejects_wider_external_budget(tmp_path):
    from source_monitor import MonitoringRuntime
    path = tmp_path / "queue.db"
    budget = AttemptBudget(str(path) + ".http-attempts.sqlite",
                           scope="nexus:worldbank:bounded-live", max_attempts=5)
    with pytest.raises(ValueError, match="binding_mismatch"):
        MonitoringRuntime(path, attempt_budget=budget)

def test_missing_live_budget_sidecar_fails_closed(tmp_path):
    from source_monitor import MonitoringRuntime
    path = tmp_path / 'queue.db'
    runtime = MonitoringRuntime(path)
    sidecar = tmp_path / 'queue.db.http-attempts.sqlite'
    assert sidecar.exists()
    runtime.attempt_budget.reserve('tick0')
    sidecar.unlink()
    with pytest.raises(RuntimeError, match='requires_recovery'):
        MonitoringRuntime(path)

def test_fixture_to_live_still_reports_source_mode_isolation(tmp_path):
    from source_monitor import MonitoringRuntime
    path = tmp_path / 'queue.db'
    MonitoringRuntime(path, transport=lambda _: b'fixture')
    with pytest.raises(ValueError, match='separate_database'):
        MonitoringRuntime(path)
