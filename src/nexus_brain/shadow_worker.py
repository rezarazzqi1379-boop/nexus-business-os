from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from .durable_queue import DurableShadowTask, InMemoryDurableShadowQueue


class ShadowWorkerError(RuntimeError):
    pass


@dataclass(frozen=True)
class ShadowWorkerResult:
    run_id: str
    task_id: str
    result_ref: str
    project_id: str


ReadOnlyExecutor = Callable[[DurableShadowTask], str]


class ShadowWorker:
    """Executes one already-governed SHADOW task without any external effect authority."""

    def __init__(self, queue: InMemoryDurableShadowQueue, worker_id: str, executor: ReadOnlyExecutor) -> None:
        if not worker_id or worker_id != worker_id.strip():
            raise ShadowWorkerError("invalid worker id")
        self.queue = queue
        self.worker_id = worker_id
        self.executor = executor

    def run_once(self, *, now: datetime, lock_seconds: int = 30) -> ShadowWorkerResult | None:
        task = self.queue.claim_next(self.worker_id, now=now, lock_seconds=lock_seconds)
        if task is None:
            return None
        env = task.envelope
        if env.execution_class != "SHADOW" or env.external_effect or env.exact_approval_ref is not None:
            raise ShadowWorkerError("worker received non-shadow or externally authorized envelope")
        try:
            result_ref = self.executor(task)
        except Exception as exc:  # task remains RUNNING until lease recovery
            raise ShadowWorkerError("read-only executor failed") from exc
        if not isinstance(result_ref, str) or not result_ref.strip() or result_ref != result_ref.strip():
            raise ShadowWorkerError("executor returned invalid result reference")
        completed = self.queue.complete_read_only(
            task.run_id,
            task.lease_token,
            self.worker_id,
            result_ref,
            now=now,
        )
        return ShadowWorkerResult(
            run_id=completed.run_id,
            task_id=completed.envelope.task_id,
            result_ref=result_ref,
            project_id=completed.envelope.project_id,
        )
