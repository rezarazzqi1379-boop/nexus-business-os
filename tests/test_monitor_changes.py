import copy
import json
from hashlib import sha256

import pytest

from source_monitor import compare_snapshots
from nexus_commercial_pilot import SOURCE
from nexus_router_runtime import PROJECT


def snapshot(rows, when="2026-10-29T10:00:00+00:00"):
    body = json.dumps(dict(rows=str(len(rows)), total=str(len(rows)), os="0", page="1", procnotices=rows))
    return dict(project_id=PROJECT, evidence_class="CLAIM", observed_at=when,
                documents=[dict(url=SOURCE, body=body, sha256=sha256(body.encode()).hexdigest())])


def row(identity="OP00476469", text="Steel bridge supply"):
    return dict(id=identity, bid_description=text, noticedate="29-Oct-2026",
                submission_deadline_date="2026-11-08T00:00:00+00:00",
                notice_type="Invitation for Bids", notice_status="Published")


def test_changed_added_absence_and_conflict():
    before = snapshot([row(), row("OP00476468")])
    after = snapshot([row(text="Steel pipe supply"), row("OP00476467"),
                      row(text="Steel plate supply")], "2026-10-29T11:00:00+00:00")
    result = compare_snapshots(before, after)
    assert result["changed"] == ["OP00476469"]
    assert result["added"] == ["OP00476467"]
    assert result["absent_from_sample"] == ["OP00476468"]
    assert result["conflicting_ids"] == ["OP00476469"]
    assert result["removed"] == [] and not result["external_action_authorized"]


def test_order_independence_dedup_and_empty_sample():
    before = snapshot([row(), row()])
    after = snapshot([row()], "2026-10-29T11:00:00+00:00")
    assert compare_snapshots(before, after)["unchanged"] == ["OP00476469"]
    assert compare_snapshots(before, snapshot([], "2026-10-29T11:00:00+00:00"))["removed"] == []
    assert compare_snapshots(None, before)["status"] == "BASELINE"


@pytest.mark.parametrize("mutation", ["digest", "scope", "url", "clock"])
def test_invalid_baseline_rejected(mutation):
    before = snapshot([row()])
    after = copy.deepcopy(before)
    after["observed_at"] = "2026-10-29T11:00:00+00:00"
    if mutation == "digest": before["documents"][0]["sha256"] = "invalid"
    if mutation == "scope": before["project_id"] = "OTHER"
    if mutation == "url": before["documents"][0]["url"] = "https://example.org/"
    if mutation == "clock": before["observed_at"] = after["observed_at"]
    with pytest.raises(ValueError): compare_snapshots(before, after)


def test_tick_uses_persisted_prior_checkpoint(tmp_path):
    from datetime import datetime, timezone
    from source_monitor import MonitoringRuntime, tick
    before = snapshot([row()])["documents"][0]["body"].encode()
    after = snapshot([row(text="Steel plate supply")])["documents"][0]["body"].encode()
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: before)
    runtime.submit("monitor_fixture_86400_0", budget_units=3)
    item = runtime.claim("seed")
    runtime.finish(item, "seed", runtime.execute(item.payload))
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: after)
    result = tick(runtime, now=datetime.now(timezone.utc).isoformat(), interval_seconds=86400)
    assert result["supervisor"] == "accepted"
    assert result["changes"]["status"] == "COMPARED"
    assert result["changes"]["changed"] == ["OP00476469"]
