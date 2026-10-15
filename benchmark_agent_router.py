"""Ten paired synthetic sequential/concurrent SQLite-queue repetitions.

No latency sleeps or LLM calls. Traced heap is Python memory, not RSS.
"""
from dataclasses import asdict
import argparse
import json
from pathlib import Path
import platform
import statistics
import tempfile
from time import perf_counter, process_time
import tracemalloc

from nexus_router_runtime import SyntheticRuntime


def benchmark():
    rows = []
    with tempfile.TemporaryDirectory() as directory:
        for repeat in range(10):
            for workers in (1, 3):
                runtime = SyntheticRuntime(Path(directory) / f"{repeat}-{workers}.db")
                task = f"proof_{repeat}_{workers}"
                runtime.submit(task)
                tracemalloc.start()
                cpu_start, wall_start = process_time(), perf_counter()
                completed = runtime.drain(workers)
                elapsed, cpu = perf_counter() - wall_start, process_time() - cpu_start
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                snapshot = runtime.snapshot()
                evidence = [e for e in snapshot["events"] if e["kind"] == "checkpoint"]
                row = {"repeat": repeat, "workers": workers, "wall_seconds": elapsed,
                       "cpu_seconds": cpu, "peak_traced_heap_bytes": peak,
                       "completion_rate": completed / 3, "error_rate": (3-completed)/3,
                       "retry_count": sum(x["attempts"]-1 for x in snapshot["tasks"]),
                       "evidence_completeness": len(evidence)/3, "review": runtime.review(task),
                       "replay_executions": SyntheticRuntime(runtime.store.path).drain(workers),
                       "model_calls": 0, "model_tokens": 0, "api_cost_usd": 0}
                assert row["review"] == "accepted" and row["completion_rate"] == 1
                assert row["error_rate"] == row["retry_count"] == row["replay_executions"] == 0
                rows.append(row)
    median = {str(n): statistics.median(x["wall_seconds"] for x in rows if x["workers"] == n)
              for n in (1,3)}
    return {"schema": "nexus.router-benchmark.v1", "python": platform.python_version(),
            "platform": platform.platform(), "repetitions_per_mode": 10,
            "median_wall_seconds": median, "sequential_over_concurrent_ratio": median['1']/median['3'],
            "session_token_usage": None, "synthetic_only": True, "rows": rows}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = benchmark()
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps({key:value for key,value in output.items() if key != "rows"}))
