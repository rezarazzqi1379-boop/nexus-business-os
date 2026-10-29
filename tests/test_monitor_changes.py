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


def complete(runtime, bucket, owner="seed", *, interval=3600):
    task = f"monitor_fixture_{interval}_{bucket}"
    runtime.submit(task, budget_units=3)
    item = runtime.claim(owner)
    assert item.payload["task_id"] == task
    runtime.finish(item, owner, runtime.execute(item.payload))
    return task


def test_predecessor_is_latest_earlier_bucket_not_last_completion(tmp_path):
    from source_monitor import MonitoringRuntime, checkpoint_pair
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: snapshot([row()])["documents"][0]["body"].encode())
    for bucket in (10, 12, 11, 14):
        complete(runtime, bucket)
    complete(runtime, 99, interval=86400)
    current = complete(runtime, 13)
    _, _, binding = checkpoint_pair(runtime, current, mode_key="fixture", interval_seconds=3600)
    assert binding["previous_task_id"] == "monitor_fixture_3600_12"
    assert binding["previous_checkpoint_seq"] < binding["current_checkpoint_seq"]


def test_late_predecessor_does_not_rewrite_replay(tmp_path):
    from source_monitor import MonitoringRuntime, checkpoint_pair
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: snapshot([row()])["documents"][0]["body"].encode())
    complete(runtime, 10)
    task = complete(runtime, 12)
    first = checkpoint_pair(runtime, task, mode_key="fixture", interval_seconds=3600)
    complete(runtime, 11)
    replay = checkpoint_pair(runtime, task, mode_key="fixture", interval_seconds=3600)
    assert first == replay
    assert replay[2]["previous_task_id"] == "monitor_fixture_3600_10"


def test_future_bucket_finishing_concurrently_is_never_predecessor(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    from source_monitor import MonitoringRuntime, checkpoint_pair
    runtime = MonitoringRuntime(tmp_path / "queue.db", transport=lambda _: snapshot([row()])["documents"][0]["body"].encode())
    complete(runtime, 10)
    items = []
    for bucket in (12, 13):
        task = f"monitor_fixture_3600_{bucket}"
        runtime.submit(task, budget_units=3)
        item = runtime.claim(str(bucket))
        items.append((item, runtime.execute(item.payload)))
    future_done = Event()
    def finish_current():
        assert future_done.wait(5)
        runtime.finish(items[0][0], "12", items[0][1])
    def finish_future():
        runtime.finish(items[1][0], "13", items[1][1])
        future_done.set()
    with ThreadPoolExecutor(max_workers=2) as pool:
        first, second = pool.submit(finish_current), pool.submit(finish_future)
        first.result(timeout=10)
        second.result(timeout=10)
    _, _, binding = checkpoint_pair(runtime, "monitor_fixture_3600_12", mode_key="fixture", interval_seconds=3600)
    assert binding["previous_task_id"] == "monitor_fixture_3600_10"


@pytest.mark.parametrize("before_text,after_text", [
    ("Steel  bridge supply", " Steel bridge supply "),
    ("Steel\u00a0bridge supply", "Steel bridge supply"),
    ("Steel cafe\u0301 supply", "Steel caf\u00e9 supply"),
])
def test_display_cosmetics_preserve_raw_evidence(before_text, after_text):
    before = snapshot([row(text=before_text)])
    after = snapshot([row(text=after_text)], "2026-10-29T11:00:00+00:00")
    result = compare_snapshots(before, after)
    assert result["changed"] == []
    assert result["cosmetic_only"] == result["raw_changed"] == ["OP00476469"]
    assert result["previous_sha256"] != result["current_sha256"]


@pytest.mark.parametrize("field,value", [
    ("bid_description", "Steel bridge supply 20 mm"),
    ("bid_description", "steel bridge supply"),
    ("submission_deadline_date", "2026-11-09T00:00:00+00:00"),
    ("notice_status", " Published "),
])
def test_meaning_and_gate_fields_are_not_normalized_away(field, value):
    updated = row()
    updated[field] = value
    result = compare_snapshots(snapshot([row()]), snapshot([updated], "2026-10-29T11:00:00+00:00"))
    assert result["changed"] == ["OP00476469"]
    assert result["cosmetic_only"] == []


def test_cosmetic_duplicate_versions_remain_conflicting():
    result = compare_snapshots(None, snapshot([row(), row(text="Steel  bridge supply")]))
    assert result["conflicting_ids"] == ["OP00476469"]


def test_serialization_order_keeps_record_content_unchanged():
    original = row()
    reordered = dict(reversed(list(original.items())))
    result = compare_snapshots(snapshot([original]), snapshot([reordered], "2026-10-29T11:00:00+00:00"))
    assert result["changed"] == result["raw_changed"] == []
    assert result["unchanged"] == [original["id"]]


def test_frozen_benchmark_invariants_and_fixture_reproducibility():
    from benchmark_source_monitor import benchmark
    first, second = benchmark(1), benchmark(1)
    assert first["fixture_sha256"] == second["fixture_sha256"]
    assert first["fixture_reads"] == first["accepted"] == 1
    assert first["external_writes"] == 0
