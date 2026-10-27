"""NEXUS isolated, dependency-free, read-only parallel routing pilot.

This module is a synthetic vertical proof, not the production supervisor.
Integrate via existing project_control_plane/AutonomyStore after review.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from time import perf_counter
from typing import Callable, Mapping
import uuid


@dataclass(frozen=True)
class WorkRequest:
    project_id: str
    task_id: str
    objective: str
    approval_required: bool = False
    action_kind: str = "READ_ONLY"


@dataclass(frozen=True)
class WorkerResult:
    worker: str
    project_id: str
    task_id: str
    status: str
    evidence: tuple[str, ...]
    detail: str


Worker = Callable[[WorkRequest], WorkerResult]
ALLOWED_ACTIONS = frozenset({"READ_ONLY", "SYNTHETIC_TEST"})


def run_parallel(
    request: WorkRequest,
    workers: Mapping[str, Worker],
    *,
    max_workers: int = 3,
) -> dict:
    """Fail closed on unsafe requests; return bounded, source-labelled results."""
    if not request.project_id or not request.task_id:
        raise ValueError("project_id and task_id are required")
    if request.approval_required or request.action_kind not in ALLOWED_ACTIONS:
        raise PermissionError("This pilot cannot execute consequential actions")
    if not 1 <= len(workers) <= 3 or not 1 <= max_workers <= 3:
        raise ValueError("Pilot supports 1-3 workers")
    if any(not name or not callable(worker) for name, worker in workers.items()):
        raise ValueError("Worker names and callables required")

    started = perf_counter()
    outcomes: dict[str, WorkerResult] = {}
    with ThreadPoolExecutor(max_workers=min(max_workers, len(workers))) as pool:
        futures = {pool.submit(worker, request): name for name, worker in workers.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                result = future.result()
                if not isinstance(result, WorkerResult):
                    raise TypeError("Worker returned invalid result")
                if (result.worker, result.project_id, result.task_id) != (
                    name, request.project_id, request.task_id
                ):
                    raise ValueError("Worker result scope mismatch")
                if result.status != "COMPLETE" or not result.evidence or any(
                    not isinstance(ref, str) or not ref.startswith(
                        f"synthetic://{request.project_id}/{request.task_id}/"
                    ) for ref in result.evidence
                ):
                    raise ValueError("Invalid synthetic evidence")
                outcomes[name] = result
            except Exception as exc:
                outcomes[name] = WorkerResult(
                    name, request.project_id, request.task_id, "FAILED", (),
                    type(exc).__name__,
                )
    return {
        "run_id": str(uuid.uuid4()),
        "project_id": request.project_id,
        "task_id": request.task_id,
        "elapsed_seconds": perf_counter() - started,
        "status": "COMPLETE" if all(x.status == "COMPLETE" for x in outcomes.values()) else "REVIEW",
        "results": {name: outcomes[name] for name in sorted(outcomes)},
    }


def synthetic_worker(name: str) -> Worker:
    def run(request: WorkRequest) -> WorkerResult:
        return WorkerResult(
            name, request.project_id, request.task_id, "COMPLETE",
            (f"synthetic://{request.project_id}/{request.task_id}/{name}",),
            f"Synthetic {name} completed; no external side effects",
        )
    return run


def demo() -> dict:
    request = WorkRequest("PRJ-NEXUS-SANDBOX", "pilot-001", "Synthetic three-way review")
    return run_parallel(request, {
        name: synthetic_worker(name)
        for name in ("research", "reconciliation", "qa")
    })
