"""One bounded public task over the existing runtime; export only a safe summary.

The private queue and full public response checkpoints live in a disposable
directory and are never CI artifacts. There are no credentials or model calls.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from nexus_public_research_agent import PublicResearchRuntime, URLS, public_get
from nexus_router_runtime import PROJECT


def require(condition):
    if not condition:
        raise ValueError("runtime_verification_failed")


def run(*, transport=None) -> dict:
    """Transport injection is for frozen tests only; the CLI has no such option."""
    reads = 0
    mode = "REAL_PUBLIC_HTTP" if transport is None else "FROZEN_TEST_FIXTURE"
    fetch = public_get if transport is None else transport
    summary = {
        "schema_version": "nexus.free-research-summary.v1",
        "status": "BLOCKED", "source_mode": mode, "project_id": PROJECT,
        "task_id": "bounded-public-research", "tasks_completed": 0,
        "supervisor": "NOT_VERIFIED", "checkpoint_integrity": False,
        "duplicate_execution_prevented": False, "http_reads_attempted": 0,
        "http_read_budget": 2, "model_tokens": 0, "external_writes": 0,
        "authority_promoted": False, "persistent_service": False,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }

    def bounded_get(url):
        nonlocal reads
        if reads >= 2:
            raise PermissionError("read_budget_exhausted")
        reads += 1
        return fetch(url)

    try:
        with TemporaryDirectory(prefix="nexus-public-research-") as directory:
            db = Path(directory) / "queue.db"
            runtime = PublicResearchRuntime(db, transport=bounded_get)
            require(runtime.submit(summary["task_id"], budget_units=3))
            require(runtime.drain(concurrency=1) == 1)
            require(runtime.review(summary["task_id"]) == "accepted")
            snapshot = runtime.snapshot()
            require(len(snapshot["tasks"]) == 1)
            require(snapshot["tasks"][0]["status"] == "completed")
            checkpoints = [json.loads(e["body"]) for e in snapshot["events"]
                           if e["task"] == summary["task_id"] and e["kind"] == "checkpoint"]
            require(len(checkpoints) == 1)
            result = checkpoints[0]
            runtime.validate_result({"task_id": summary["task_id"]}, result)
            # Reopen the durable store and replay submission without another GET.
            recovered = PublicResearchRuntime(db, transport=bounded_get)
            require(not recovered.submit(summary["task_id"], budget_units=3))
            require(recovered.drain(concurrency=1) == 0)
            require(recovered.review(summary["task_id"]) == "accepted")
            require(reads == 2)
            summary.update(status="VERIFIED", tasks_completed=1, supervisor="accepted",
                checkpoint_integrity=True, duplicate_execution_prevented=True,
                evidence_class="CLAIM", sources=[{"url": url, "sha256": doc["sha256"]}
                    for url, doc in zip(URLS, result["documents"])])
    except Exception:
        # Provider responses, paths, DB contents and raw exception text never leave.
        summary["reason"] = "bounded_research_or_verification_failed"
    summary["http_reads_attempted"] = reads
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", type=Path, required=True)
    args = parser.parse_args()
    summary = run()
    text = json.dumps(summary, sort_keys=True, indent=2) + "\n"
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0 if summary["status"] == "VERIFIED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
