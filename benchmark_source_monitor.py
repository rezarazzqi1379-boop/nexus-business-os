"""Offline reproducible end-to-end benchmark; no live network or promotion."""
import json
import platform
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from time import perf_counter, process_time

from source_monitor import MonitoringRuntime, tick


def benchmark(iterations=20):
    if type(iterations) is not int or not 1 <= iterations <= 100:
        raise ValueError("invalid_iteration_budget")
    now = datetime.now(timezone.utc)
    row = dict(id="OP00476469", bid_description="Steel bridge supply",
               noticedate=now.strftime("%d-%b-%Y"),
               submission_deadline_date=(now + timedelta(days=10)).isoformat(),
               notice_type="Invitation for Bids", notice_status="Published")
    body = json.dumps(dict(rows="2", total="2", os="0", page="1", procnotices=[row, row])).encode()
    started, cpu = perf_counter(), process_time()
    reads, accepted = [], 0
    with tempfile.TemporaryDirectory() as temp:
        for i in range(iterations):
            runtime = MonitoringRuntime(Path(temp) / f"{i}.db", transport=lambda _: reads.append(1) or body)
            first = tick(runtime, now=datetime.now(timezone.utc).isoformat(), interval_seconds=86400)
            second = tick(runtime, now=datetime.now(timezone.utc).isoformat(), interval_seconds=86400)
            assert first["assessment"]["duplicates_removed"] == 1
            assert first["changes"]["status"] == "BASELINE"
            assert not second["work_attempted"]
            assert first["assessment"]["actionable_opportunities"] == 0
            accepted += first["supervisor"] == "accepted"
    return dict(iterations=iterations, accepted=accepted, fixture_reads=len(reads),
                elapsed_seconds=perf_counter()-started, cpu_seconds=process_time()-cpu,
                python=platform.python_version(), fixture_bytes=len(body),
                external_writes=0, mode="OFFLINE_FIXTURE", market_accuracy="UNKNOWN")


if __name__ == "__main__":
    print(json.dumps(benchmark(), indent=2))
