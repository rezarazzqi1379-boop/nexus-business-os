"""Offline reproducible end-to-end benchmark; no live network or promotion."""
import json
import platform
import tempfile
import argparse
import os
import sqlite3
import subprocess
from hashlib import sha256
from importlib.metadata import version
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter, process_time

from source_monitor import MonitoringRuntime, tick


def benchmark(iterations=20):
    if type(iterations) is not int or not 1 <= iterations <= 100:
        raise ValueError("invalid_iteration_budget")
    row = dict(id="OP00476469", bid_description="Steel bridge supply",
               noticedate="29-Oct-2026",
               submission_deadline_date="2026-11-08T00:00:00+00:00",
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
    assert accepted == iterations and len(reads) == iterations
    return dict(iterations=iterations, accepted=accepted, fixture_reads=len(reads),
                elapsed_seconds=perf_counter()-started, cpu_seconds=process_time()-cpu,
                python=platform.python_version(), fixture_bytes=len(body),
                fixture_sha256=sha256(body).hexdigest(),
                external_writes=0, mode="OFFLINE_FIXTURE", market_accuracy="UNKNOWN")


def environment_evidence(context):
    root = Path(__file__).resolve().parent
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, check=True,
                          capture_output=True, text=True, timeout=5).stdout.strip()
    files = ("source_monitor.py", "benchmark_source_monitor.py", "nexus_commercial_pilot.py",
             "tests/test_monitor_changes.py", "tests/test_source_monitor.py",
             ".github/workflows/source-monitor.yml")
    diff = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *files], cwd=root,
                          capture_output=True, timeout=5)
    if diff.returncode not in (0, 1):
        raise ValueError("code_binding_unavailable")
    return dict(schema_version="nexus.monitor-benchmark.v2", context=context,
                observed_at=datetime.now(timezone.utc).isoformat(), git_head=head,
                code_matches_head=diff.returncode == 0,
                code_sha256={name: sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                             for name in files},
                code_hash_policy="LF-normalized repository bytes", os=platform.system(),
                os_release=platform.release(), machine=platform.machine(),
                python=platform.python_version(), sqlite=sqlite3.sqlite_version,
                test_dependencies={"pytest": version("pytest")},
                ci={key: os.environ.get(key) for key in
                    ("GITHUB_RUN_ID", "GITHUB_RUN_ATTEMPT", "GITHUB_REPOSITORY", "GITHUB_JOB")}
                if context == "ci" else None,
                production_target_verified=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", choices=("local", "ci"), default="local")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {**environment_evidence(args.context), **benchmark()}
    text = json.dumps(report, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text + "\n", encoding="utf-8")
    print(text)
