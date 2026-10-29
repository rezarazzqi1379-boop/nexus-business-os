from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json

import pytest

from source_monitor import MonitoringRuntime, SourceObservation, compare_sources, tick
from nexus_commercial_pilot import SOURCE, LANE
from nexus_connector_control_plane import (
    ConnectorManifest, ConnectorSnapshot, ConnectorState, EvidenceEnvelope, EvidenceClass,
)
from nexus_router_runtime import PROJECT


def now():
    return datetime.now(timezone.utc).isoformat()


def body():
    row = dict(id="OP00476469", bid_description="Steel bridge supply",
               noticedate=datetime.now(timezone.utc).strftime("%d-%b-%Y"),
               submission_deadline_date=(datetime.now(timezone.utc) + timedelta(days=10)).isoformat(),
               notice_type="Invitation for Bids", notice_status="Published")
    return json.dumps(dict(rows="2", os="0", page="1", total="2", procnotices=[row, row])).encode()


def observation(connector, group, *, value="open", project=PROJECT, observed=None):
    observed = observed or now()
    return SourceObservation(
        ConnectorManifest(connector, connector, ("read",), (PROJECT,), True, False, 300), group,
        (EvidenceEnvelope(connector + "-1", connector, project, LANE + ":notice:OP00476469",
                          value, EvidenceClass.CLAIM, "https://example.org/notice", observed),),
        ConnectorSnapshot(connector, observed, ConnectorState.AVAILABLE))


def test_persisted_tick_restart_dedup_and_provenance(tmp_path):
    calls = []
    transport = lambda url: calls.append(url) or body()
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=transport)
    first = tick(runtime, now=now(), interval_seconds=86400)
    assert first["supervisor"] == "accepted" and first["status"] == "ACCEPTED"
    assert first["assessment"]["duplicates_removed"] == 1
    assert first["assessment"]["actionable_opportunities"] == 0
    assert first["source_comparison"]["preflight"]["gate"] == "SAFE"
    assert first["source_comparison"]["claims"][0]["status"] == "INDEPENDENT_SOURCE_MISSING"
    assert first["provenance"][0]["source_url"] == SOURCE
    assert first["provenance"][0]["lane_id"] == LANE
    assert first["provenance"][0]["status"] == "CANDIDATE_NOT_ACTIVATED"
    second = tick(MonitoringRuntime(tmp_path / "queue.db", transport=transport), now=now(), interval_seconds=86400)
    assert not second["submitted"] and second["completed_queue_items"] == 0
    assert calls == [SOURCE]
    assert first["external_writes"] == 0 and not first["scheduler_active"]


def test_concurrent_tick_reads_once(tmp_path):
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda url: body())
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = list(pool.map(lambda _: tick(runtime, now=now(), interval_seconds=86400), range(3)))
    assert sum(r["submitted"] for r in results) == 1
    assert sum(r["completed_queue_items"] for r in results) == 1


def test_transport_failure_redacted_and_backoff(tmp_path):
    calls = []
    def broken(url):
        calls.append(url)
        raise RuntimeError("private-provider-body")
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=broken)
    result = tick(runtime, now=now(), interval_seconds=86400)
    assert result["status"] == "WAITING_OR_BLOCKED"
    tick(runtime, now=now(), interval_seconds=86400)
    assert len(calls) == 1
    assert "private-provider-body" not in json.dumps(runtime.snapshot())


def test_stop_prevents_read(tmp_path):
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: pytest.fail("unexpected read"))
    runtime.stop()
    assert tick(runtime, now=now())["completed_queue_items"] == 0


def test_fixture_database_cannot_be_relabelled_live(tmp_path):
    MonitoringRuntime(tmp_path / "queue.db", transport=lambda url: body())
    with pytest.raises(ValueError, match="separate_database"):
        MonitoringRuntime(tmp_path / "queue.db")


def test_lane_cannot_cross_source_comparison():
    source = observation("one", "a")
    source = replace(source, evidence=(replace(source.evidence[0], semantic_key="other:notice:OP00476469"),))
    with pytest.raises(ValueError, match="lane_binding"):
        compare_sources((source,), now=now())


@pytest.mark.parametrize("interval", [True, 0, 299, 86401])
def test_interval_budget(tmp_path, interval):
    with pytest.raises(ValueError):
        tick(MonitoringRuntime(tmp_path / "queue.db"), now=now(), interval_seconds=interval)


@pytest.mark.parametrize("groups,status", [
    (("owner-a", "owner-b"), "CORROBORATED_CLAIM"),
    (("mirror-owner", "mirror-owner"), "INDEPENDENT_SOURCE_MISSING"),
    ((None, None), "INDEPENDENT_SOURCE_MISSING"),
])
def test_independent_claim_convergence(groups, status):
    result = compare_sources((observation("one", groups[0]), observation("two", groups[1])), now=now())
    claim = result["claims"][0]
    assert claim["status"] == status and claim["evidence_class"] == "CLAIM"
    assert claim["decision"] == "INVESTIGATE" and not result["external_action_authorized"]


def test_conflict_cannot_be_hidden_by_duplicate_sources():
    result = compare_sources((observation("one", "a"), observation("two", "b", value="closed")), now=now())
    assert result["claims"][0]["decision"] == "REJECT"
    assert result["claims"][0]["status"] == "CONFLICT"


@pytest.mark.parametrize("bad", ["scope", "stale", "future", "unavailable", "binding", "fact"])
def test_invalid_evidence_fails_closed(bad):
    source = observation("one", "a")
    if bad == "scope":
        source = replace(source, evidence=(replace(source.evidence[0], project_id="other"),))
    elif bad in {"stale", "future"}:
        stamp = (datetime.now(timezone.utc) + timedelta(seconds=-600 if bad == "stale" else 600)).isoformat()
        source = observation("one", "a", observed=stamp)
    elif bad == "unavailable":
        source = replace(source, snapshot=replace(source.snapshot, state=ConnectorState.UNAVAILABLE))
    elif bad == "binding":
        source = replace(source, evidence=(replace(source.evidence[0], connector_id="forged"),))
    else:
        source = replace(source, evidence=(replace(source.evidence[0], classification=EvidenceClass.FACT),))
    if bad in {"binding", "fact"}:
        with pytest.raises(ValueError):
            compare_sources((source,), now=now())
    else:
        assert compare_sources((source,), now=now())["claims"][0]["decision"] == "REJECT"
