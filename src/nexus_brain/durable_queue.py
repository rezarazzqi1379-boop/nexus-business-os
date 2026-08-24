from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from typing import Protocol
import uuid

from .execution_bridge import ShadowExecutionEnvelope


class DurableQueueError(ValueError):
    pass


class QueueOwnershipError(DurableQueueError):
    pass


class IdempotencyConflictError(DurableQueueError):
    pass


@dataclass(frozen=True)
class DurableShadowTask:
    run_id: str
    envelope: ShadowExecutionEnvelope
    status: str = "PENDING"
    task_version: int = 1
    lease_token: str | None = None
    lease_owner: str | None = None
    lock_expires_at: datetime | None = None
    result_ref: str | None = None


class DurableShadowQueue(Protocol):
    def enqueue(self, envelope: ShadowExecutionEnvelope) -> DurableShadowTask: ...
    def claim_next(self, worker: str, *, now: datetime, lock_seconds: int = 30) -> DurableShadowTask | None: ...
    def complete_read_only(self, run_id: str, lease_token: str, worker: str, result_ref: str, *, now: datetime) -> DurableShadowTask: ...
    def recover_expired(self, *, now: datetime) -> tuple[DurableShadowTask, ...]: ...


def _aware(dt: datetime) -> None:
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise DurableQueueError("queue timestamps must be timezone-aware")


def _valid_text(value: str, name: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DurableQueueError(f"invalid {name}")


class InMemoryDurableShadowQueue:
    """Reference semantics for the future PostgreSQL shadow queue.

    This queue intentionally accepts only already-validated ShadowExecutionEnvelope
    values. It has no approval or external-effect API.
    """

    def __init__(self) -> None:
        self._by_run: dict[str, DurableShadowTask] = {}
        self._by_idempotency: dict[str, str] = {}

    def enqueue(self, envelope: ShadowExecutionEnvelope) -> DurableShadowTask:
        if envelope.execution_class != "SHADOW" or envelope.external_effect or envelope.exact_approval_ref is not None:
            raise DurableQueueError("durable v0.1 queue accepts shadow-only envelopes")
        existing_run = self._by_idempotency.get(envelope.idempotency_key)
        if existing_run:
            existing = self._by_run[existing_run]
            if existing.envelope != envelope:
                raise IdempotencyConflictError("idempotency key rebound to a different immutable envelope")
            return existing
        task = DurableShadowTask(run_id=str(uuid.uuid4()), envelope=envelope)
        self._by_run[task.run_id] = task
        self._by_idempotency[envelope.idempotency_key] = task.run_id
        return task

    def claim_next(self, worker: str, *, now: datetime, lock_seconds: int = 30) -> DurableShadowTask | None:
        _valid_text(worker, "worker")
        _aware(now)
        if lock_seconds <= 0:
            raise DurableQueueError("lock_seconds must be positive")
        for run_id, task in self._by_run.items():
            expired = task.status == "RUNNING" and task.lock_expires_at is not None and task.lock_expires_at <= now
            if task.status != "PENDING" and not expired:
                continue
            claimed = replace(
                task,
                status="RUNNING",
                task_version=task.task_version + 1,
                lease_token=str(uuid.uuid4()),
                lease_owner=worker,
                lock_expires_at=now + timedelta(seconds=lock_seconds),
            )
            self._by_run[run_id] = claimed
            return claimed
        return None

    def complete_read_only(self, run_id: str, lease_token: str, worker: str, result_ref: str, *, now: datetime) -> DurableShadowTask:
        _valid_text(result_ref, "result_ref")
        _aware(now)
        task = self._by_run.get(run_id)
        if (
            task is None
            or task.status != "RUNNING"
            or task.lease_token != lease_token
            or task.lease_owner != worker
            or task.lock_expires_at is None
            or task.lock_expires_at <= now
        ):
            raise QueueOwnershipError("lease invalid, expired, or not current owner")
        completed = replace(
            task,
            status="COMPLETED",
            lease_token=None,
            lease_owner=None,
            lock_expires_at=None,
            result_ref=result_ref,
        )
        self._by_run[run_id] = completed
        return completed

    def recover_expired(self, *, now: datetime) -> tuple[DurableShadowTask, ...]:
        _aware(now)
        recovered: list[DurableShadowTask] = []
        for run_id, task in list(self._by_run.items()):
            if task.status == "RUNNING" and task.lock_expires_at is not None and task.lock_expires_at <= now:
                item = replace(
                    task,
                    status="PENDING",
                    task_version=task.task_version + 1,
                    lease_token=None,
                    lease_owner=None,
                    lock_expires_at=None,
                )
                self._by_run[run_id] = item
                recovered.append(item)
        return tuple(recovered)

    def get(self, run_id: str) -> DurableShadowTask:
        return self._by_run[run_id]
