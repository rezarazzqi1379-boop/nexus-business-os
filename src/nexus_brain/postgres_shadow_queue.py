from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import json
import uuid

from .durable_queue import DurableQueueError, DurableShadowTask, IdempotencyConflictError, QueueOwnershipError
from .execution_bridge import ShadowExecutionEnvelope

try:
    import psycopg
    from psycopg.rows import dict_row
except ImportError:  # pragma: no cover - exercised by packaging boundary
    psycopg = None
    dict_row = None


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS nexus_shadow_tasks (
  run_id uuid PRIMARY KEY,
  task_id text NOT NULL,
  idempotency_key text NOT NULL UNIQUE,
  envelope_json jsonb NOT NULL,
  status text NOT NULL CHECK (status IN ('PENDING','RUNNING','COMPLETED')),
  task_version bigint NOT NULL DEFAULT 1,
  lease_token uuid,
  lease_owner text,
  lock_expires_at timestamptz,
  result_ref text,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_nexus_shadow_claim
  ON nexus_shadow_tasks(status, lock_expires_at, created_at);
"""


class PostgresShadowQueue:
    """PostgreSQL-backed SHADOW-only queue.

    The store owns durable execution state only. It does not contain approvals,
    provider-operation journals, external-effect APIs, or business/source authority.
    """

    def __init__(self, dsn: str):
        if psycopg is None:
            raise RuntimeError("PostgreSQL support requires the optional psycopg dependency")
        if not isinstance(dsn, str) or not dsn.strip() or dsn != dsn.strip():
            raise DurableQueueError("invalid PostgreSQL DSN")
        self.dsn = dsn

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def migrate(self) -> None:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)

    @staticmethod
    def _validate_envelope(envelope: ShadowExecutionEnvelope) -> None:
        if envelope.execution_class != "SHADOW" or envelope.external_effect or envelope.exact_approval_ref is not None:
            raise DurableQueueError("PostgreSQL v0.1 queue accepts shadow-only envelopes")

    @staticmethod
    def _serialize(envelope: ShadowExecutionEnvelope) -> str:
        return json.dumps(asdict(envelope), sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _deserialize(payload) -> ShadowExecutionEnvelope:
        if isinstance(payload, str):
            payload = json.loads(payload)
        return ShadowExecutionEnvelope(**payload)

    @classmethod
    def _task_from_row(cls, row) -> DurableShadowTask:
        return DurableShadowTask(
            run_id=str(row["run_id"]),
            envelope=cls._deserialize(row["envelope_json"]),
            status=row["status"],
            task_version=row["task_version"],
            lease_token=str(row["lease_token"]) if row["lease_token"] else None,
            lease_owner=row["lease_owner"],
            lock_expires_at=row["lock_expires_at"],
            result_ref=row["result_ref"],
        )

    def enqueue(self, envelope: ShadowExecutionEnvelope) -> DurableShadowTask:
        self._validate_envelope(envelope)
        raw = self._serialize(envelope)
        run_id = uuid.uuid4()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO nexus_shadow_tasks
                       (run_id,task_id,idempotency_key,envelope_json,status)
                       VALUES(%s,%s,%s,%s::jsonb,'PENDING')
                       ON CONFLICT(idempotency_key) DO NOTHING
                       RETURNING *""",
                    (run_id, envelope.task_id, envelope.idempotency_key, raw),
                )
                row = cur.fetchone()
                if row:
                    return self._task_from_row(row)
                cur.execute(
                    "SELECT * FROM nexus_shadow_tasks WHERE idempotency_key=%s FOR UPDATE",
                    (envelope.idempotency_key,),
                )
                existing = cur.fetchone()
                if not existing:
                    raise IdempotencyConflictError("idempotency race left no existing task")
                if self._serialize(self._deserialize(existing["envelope_json"])) != raw:
                    raise IdempotencyConflictError("idempotency key rebound to a different immutable envelope")
                return self._task_from_row(existing)

    def claim_next(self, worker: str, *, now: datetime, lock_seconds: int = 30) -> DurableShadowTask | None:
        if not isinstance(worker, str) or not worker.strip() or worker != worker.strip():
            raise DurableQueueError("invalid worker")
        if now.tzinfo is None or now.utcoffset() is None:
            raise DurableQueueError("queue timestamps must be timezone-aware")
        if lock_seconds <= 0:
            raise DurableQueueError("lock_seconds must be positive")
        token = uuid.uuid4()
        expiry = now + timedelta(seconds=lock_seconds)
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT run_id,status,task_version FROM nexus_shadow_tasks
                       WHERE status='PENDING' OR (status='RUNNING' AND lock_expires_at <= %s)
                       ORDER BY created_at
                       FOR UPDATE SKIP LOCKED
                       LIMIT 1""",
                    (now,),
                )
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute(
                    """UPDATE nexus_shadow_tasks
                       SET status='RUNNING', task_version=task_version+1,
                           lease_token=%s, lease_owner=%s, lock_expires_at=%s
                       WHERE run_id=%s AND status=%s AND task_version=%s
                       RETURNING *""",
                    (token, worker, expiry, row["run_id"], row["status"], row["task_version"]),
                )
                claimed = cur.fetchone()
                return self._task_from_row(claimed) if claimed else None

    def complete_read_only(self, run_id: str, lease_token: str, worker: str, result_ref: str, *, now: datetime) -> DurableShadowTask:
        if not isinstance(result_ref, str) or not result_ref.strip() or result_ref != result_ref.strip():
            raise DurableQueueError("invalid result_ref")
        if now.tzinfo is None or now.utcoffset() is None:
            raise DurableQueueError("queue timestamps must be timezone-aware")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE nexus_shadow_tasks
                       SET status='COMPLETED', lease_token=NULL, lease_owner=NULL,
                           lock_expires_at=NULL, result_ref=%s
                       WHERE run_id=%s::uuid AND status='RUNNING'
                         AND lease_token=%s::uuid AND lease_owner=%s
                         AND lock_expires_at > %s
                       RETURNING *""",
                    (result_ref, run_id, lease_token, worker, now),
                )
                row = cur.fetchone()
                if not row:
                    raise QueueOwnershipError("lease invalid, expired, or not current owner")
                return self._task_from_row(row)

    def recover_expired(self, *, now: datetime) -> tuple[DurableShadowTask, ...]:
        if now.tzinfo is None or now.utcoffset() is None:
            raise DurableQueueError("queue timestamps must be timezone-aware")
        recovered: list[DurableShadowTask] = []
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE nexus_shadow_tasks
                       SET status='PENDING', task_version=task_version+1,
                           lease_token=NULL, lease_owner=NULL, lock_expires_at=NULL
                       WHERE status='RUNNING' AND lock_expires_at <= %s
                       RETURNING *""",
                    (now,),
                )
                recovered.extend(self._task_from_row(row) for row in cur.fetchall())
        return tuple(recovered)

    def get(self, run_id: str) -> DurableShadowTask:
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM nexus_shadow_tasks WHERE run_id=%s::uuid", (run_id,))
                row = cur.fetchone()
                if not row:
                    raise KeyError(run_id)
                return self._task_from_row(row)
