import os, uuid
from datetime import datetime, timezone, timedelta

import psycopg
from psycopg.rows import dict_row


def utcnow():
    return datetime.now(timezone.utc)


class PostgresPLOError(Exception):
    pass


class PostgresOwnershipError(PostgresPLOError):
    pass


class PostgresApprovalError(PostgresPLOError):
    pass


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS plo_tasks (
  run_id uuid PRIMARY KEY,
  task_id text NOT NULL,
  idempotency_key text NOT NULL UNIQUE,
  status text NOT NULL CHECK (status IN ('PENDING','RUNNING','COMPLETED','FAILED','CANCELLED')),
  task_version bigint NOT NULL DEFAULT 1,
  approval_required boolean NOT NULL DEFAULT false,
  lease_token uuid,
  lease_owner text,
  lock_expires_at timestamptz,
  retry_count integer NOT NULL DEFAULT 0,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_plo_tasks_claim ON plo_tasks(status, lock_expires_at, created_at);

CREATE TABLE IF NOT EXISTS plo_approvals (
  approval_id uuid PRIMARY KEY,
  run_id uuid NOT NULL REFERENCES plo_tasks(run_id) ON DELETE CASCADE,
  task_version bigint NOT NULL,
  scope text NOT NULL,
  decision text CHECK (decision IN ('approved','denied') OR decision IS NULL),
  expires_at timestamptz NOT NULL,
  consumed_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_plo_approvals_lookup ON plo_approvals(run_id, task_version, scope);

CREATE TABLE IF NOT EXISTS plo_operations (
  operation_key text PRIMARY KEY,
  run_id uuid NOT NULL REFERENCES plo_tasks(run_id) ON DELETE CASCADE,
  scope text NOT NULL,
  auth_token uuid NOT NULL,
  state text NOT NULL CHECK (state IN ('authorized','intended','executed','acknowledged')),
  created_at timestamptz NOT NULL DEFAULT now(),
  executed_at timestamptz
);

CREATE TABLE IF NOT EXISTS plo_execution_log (
  id bigserial PRIMARY KEY,
  operation_key text NOT NULL,
  run_id uuid NOT NULL,
  executed_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS plo_audit (
  id bigserial PRIMARY KEY,
  ts timestamptz NOT NULL DEFAULT now(),
  action text NOT NULL,
  run_id uuid,
  result text
);
"""


class PostgresPLOStore:
    def __init__(self, dsn: str):
        self.dsn = dsn

    @classmethod
    def from_env(cls):
        dsn = os.getenv("NEXUS_PLO_DATABASE_URL")
        if not dsn:
            raise RuntimeError("NEXUS_PLO_DATABASE_URL is required")
        return cls(dsn)

    def connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def migrate(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)

    def reset_for_tests(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("TRUNCATE plo_execution_log, plo_operations, plo_approvals, plo_tasks, plo_audit RESTART IDENTITY CASCADE")

    def enqueue(self, task_id: str, idempotency_key: str, approval_required: bool = False):
        rid = uuid.uuid4()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO plo_tasks(run_id,task_id,idempotency_key,status,approval_required)
                       VALUES(%s,%s,%s,'PENDING',%s)
                       ON CONFLICT(idempotency_key) DO NOTHING
                       RETURNING run_id""",
                    (rid, task_id, idempotency_key, approval_required),
                )
                row = cur.fetchone()
                if row:
                    cur.execute("INSERT INTO plo_audit(action,run_id,result) VALUES('enqueue',%s,'created')", (row['run_id'],))
                    return str(row["run_id"])
                cur.execute("SELECT run_id FROM plo_tasks WHERE idempotency_key=%s", (idempotency_key,))
                return str(cur.fetchone()["run_id"])

    def claim_next(self, worker: str, lock_seconds: int = 30):
        token = uuid.uuid4()
        expiry = utcnow() + timedelta(seconds=lock_seconds)
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT run_id,status,task_version FROM plo_tasks
                       WHERE status='PENDING' OR (status='RUNNING' AND lock_expires_at < now())
                       ORDER BY created_at
                       FOR UPDATE SKIP LOCKED
                       LIMIT 1"""
                )
                row = cur.fetchone()
                if not row:
                    return None
                cur.execute(
                    """UPDATE plo_tasks SET status='RUNNING', task_version=task_version+1,
                       lease_token=%s, lease_owner=%s, lock_expires_at=%s
                       WHERE run_id=%s AND status=%s AND task_version=%s
                       RETURNING run_id,task_version""",
                    (token, worker, expiry, row["run_id"], row["status"], row["task_version"]),
                )
                claimed = cur.fetchone()
                if not claimed:
                    return None
                return {"run_id": str(claimed["run_id"]), "_lease_token": str(token), "task_version": claimed["task_version"]}

    def renew_lease(self, run_id: str, lease_token: str, worker: str, extend_seconds: int = 30):
        new_expiry = utcnow() + timedelta(seconds=extend_seconds)
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE plo_tasks SET lock_expires_at=%s
                       WHERE run_id=%s::uuid AND status='RUNNING' AND lease_token=%s::uuid
                       AND lease_owner=%s AND lock_expires_at > now()
                       RETURNING run_id""",
                    (new_expiry, run_id, lease_token, worker),
                )
                if not cur.fetchone():
                    raise PostgresOwnershipError("lease invalid, expired, or no longer owned")

    def request_approval(self, run_id: str, scope: str, ttl_seconds: int = 3600):
        aid = uuid.uuid4()
        expiry = utcnow() + timedelta(seconds=ttl_seconds)
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT task_version FROM plo_tasks WHERE run_id=%s::uuid", (run_id,))
                row = cur.fetchone()
                if not row:
                    raise PostgresApprovalError("missing task")
                cur.execute(
                    "INSERT INTO plo_approvals(approval_id,run_id,task_version,scope,expires_at) VALUES(%s,%s::uuid,%s,%s,%s)",
                    (aid, run_id, row["task_version"], scope, expiry),
                )
        return str(aid)

    def decide_approval(self, approval_id: str, decision: str):
        if decision not in ("approved", "denied"):
            raise PostgresApprovalError("bad decision")
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE plo_approvals SET decision=%s WHERE approval_id=%s::uuid AND decision IS NULL RETURNING approval_id",
                    (decision, approval_id),
                )
                if not cur.fetchone():
                    raise PostgresApprovalError("missing or already decided")

    def authorize_operation(self, run_id: str, operation_key: str, scope: str, lease_token: str, worker: str):
        auth = uuid.uuid4()
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT status,lease_token,lease_owner,lock_expires_at,task_version,approval_required FROM plo_tasks WHERE run_id=%s::uuid FOR UPDATE",
                    (run_id,),
                )
                task = cur.fetchone()
                if (not task or task["status"] != "RUNNING" or str(task["lease_token"]) != lease_token
                        or task["lease_owner"] != worker or task["lock_expires_at"] is None
                        or task["lock_expires_at"] <= utcnow()):
                    raise PostgresOwnershipError("lease invalid, expired, or not current owner")
                if not task["approval_required"]:
                    raise PostgresApprovalError("approval path misuse")
                cur.execute("SELECT run_id,scope FROM plo_operations WHERE operation_key=%s", (operation_key,))
                existing = cur.fetchone()
                if existing and (str(existing["run_id"]) != run_id or existing["scope"] != scope):
                    raise PostgresApprovalError("operation key rebound")
                cur.execute(
                    """SELECT approval_id FROM plo_approvals
                       WHERE run_id=%s::uuid AND task_version=%s AND scope=%s AND decision='approved'
                       AND consumed_at IS NULL AND expires_at > now()
                       ORDER BY created_at LIMIT 1 FOR UPDATE""",
                    (run_id, task["task_version"], scope),
                )
                approval = cur.fetchone()
                if not approval:
                    raise PostgresApprovalError("no valid exact-scope/version approval")
                cur.execute("UPDATE plo_approvals SET consumed_at=now() WHERE approval_id=%s", (approval["approval_id"],))
                cur.execute(
                    "INSERT INTO plo_operations(operation_key,run_id,scope,auth_token,state) VALUES(%s,%s::uuid,%s,%s,'authorized')",
                    (operation_key, run_id, scope, auth),
                )
                cur.execute("INSERT INTO plo_audit(action,run_id,result) VALUES('operation_authorized',%s::uuid,%s)", (run_id, operation_key))
        return str(auth)

    def record_intent(self, run_id: str, operation_key: str, auth_token: str, lease_token: str, worker: str):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT status,lease_token,lease_owner,lock_expires_at FROM plo_tasks
                       WHERE run_id=%s::uuid FOR UPDATE""",
                    (run_id,),
                )
                task = cur.fetchone()
                if (not task or task["status"] != "RUNNING" or str(task["lease_token"]) != lease_token
                        or task["lease_owner"] != worker or task["lock_expires_at"] is None
                        or task["lock_expires_at"] <= utcnow()):
                    raise PostgresOwnershipError("lease invalid, expired, or not current owner")
                cur.execute(
                    """UPDATE plo_operations SET state='intended'
                       WHERE operation_key=%s AND run_id=%s::uuid AND auth_token=%s::uuid AND state='authorized'
                       RETURNING operation_key""",
                    (operation_key, run_id, auth_token),
                )
                if not cur.fetchone():
                    raise PostgresApprovalError("missing prior authorization")

    def mark_executed(self, operation_key: str):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT run_id,state FROM plo_operations WHERE operation_key=%s FOR UPDATE", (operation_key,))
                row = cur.fetchone()
                if not row:
                    raise PostgresApprovalError("unknown operation")
                if row["state"] == "executed":
                    return False
                if row["state"] != "intended":
                    raise PostgresApprovalError("operation was not intended")
                cur.execute(
                    "UPDATE plo_operations SET state='executed', executed_at=now() WHERE operation_key=%s AND state='intended' RETURNING run_id",
                    (operation_key,),
                )
                changed = cur.fetchone()
                if not changed:
                    raise PostgresApprovalError("execution state changed concurrently")
                cur.execute("INSERT INTO plo_execution_log(operation_key,run_id) VALUES(%s,%s)", (operation_key, row["run_id"]))
                return True

    def recover_orphans(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """UPDATE plo_tasks SET status='PENDING',task_version=task_version+1,
                       lease_token=NULL,lease_owner=NULL,lock_expires_at=NULL,retry_count=retry_count+1
                       WHERE status='RUNNING' AND lock_expires_at < now()
                       RETURNING run_id"""
                )
                return [str(r["run_id"]) for r in cur.fetchall()]

    def metrics(self):
        with self.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT count(*) AS n FROM (SELECT operation_key FROM plo_execution_log GROUP BY operation_key HAVING count(*)>1) x")
                dup = cur.fetchone()["n"]
                cur.execute("SELECT count(*) AS n FROM plo_tasks WHERE status='PENDING'")
                pending = cur.fetchone()["n"]
                return {"duplicate_execution_count": dup, "pending": pending}
