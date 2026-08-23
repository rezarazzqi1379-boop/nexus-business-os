import contextlib, sqlite3, uuid
from datetime import datetime, timezone, timedelta

STATES={"PENDING","RUNNING","COMPLETED","FAILED","CANCELLED"}

def now(): return datetime.now(timezone.utc).isoformat()
class PLOError(Exception): pass
class OwnershipError(PLOError): pass
class ApprovalError(PLOError): pass

class PLOStore:
    def __init__(self,path): self.path=path; self._init()
    @contextlib.contextmanager
    def tx(self):
        db=sqlite3.connect(self.path,timeout=10,isolation_level=None)
        db.execute("PRAGMA journal_mode=WAL"); db.execute("PRAGMA busy_timeout=5000")
        try:
            db.execute("BEGIN IMMEDIATE"); yield db; db.execute("COMMIT")
        except Exception:
            db.execute("ROLLBACK"); raise
        finally: db.close()
    def _init(self):
        db=sqlite3.connect(self.path)
        try:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS tasks(
              run_id TEXT PRIMARY KEY, task_id TEXT NOT NULL, idempotency_key TEXT UNIQUE NOT NULL,
              status TEXT NOT NULL, task_version INTEGER NOT NULL DEFAULT 1,
              approval_required INTEGER NOT NULL DEFAULT 0,
              lease_token TEXT, lease_owner TEXT, lock_expires_at TEXT, retry_count INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE IF NOT EXISTS approvals(
              approval_id TEXT PRIMARY KEY, run_id TEXT NOT NULL, task_version INTEGER NOT NULL,
              scope TEXT NOT NULL, decision TEXT, expires_at TEXT NOT NULL, consumed_at TEXT);
            CREATE TABLE IF NOT EXISTS operations(
              operation_key TEXT PRIMARY KEY, run_id TEXT NOT NULL, scope TEXT NOT NULL,
              auth_token TEXT NOT NULL, state TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS execution_log(
              id INTEGER PRIMARY KEY AUTOINCREMENT, operation_key TEXT NOT NULL, ts TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(
              id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT NOT NULL, action TEXT NOT NULL,
              run_id TEXT, result TEXT);
            ''')
            db.commit()
        finally:
            db.close()
    def audit(self,db,action,run_id=None,result=None):
        db.execute("INSERT INTO audit(ts,action,run_id,result) VALUES(?,?,?,?)",(now(),action,run_id,result))
    def enqueue(self,task_id,idempotency_key,approval_required=False):
        with self.tx() as db:
            row=db.execute("SELECT run_id FROM tasks WHERE idempotency_key=?",(idempotency_key,)).fetchone()
            if row: return row[0]
            rid=str(uuid.uuid4())
            db.execute("INSERT INTO tasks(run_id,task_id,idempotency_key,status,approval_required) VALUES(?,?,?,?,?)",
                       (rid,task_id,idempotency_key,"PENDING",int(approval_required)))
            self.audit(db,"enqueue",rid,"created"); return rid
    def claim_next(self,worker,lock_seconds=30):
        with self.tx() as db:
            n=now()
            row=db.execute("SELECT run_id,status,task_version FROM tasks WHERE status='PENDING' OR (status='RUNNING' AND lock_expires_at<?) ORDER BY rowid LIMIT 1",(n,)).fetchone()
            if not row: return None
            rid,status,ver=row; token=str(uuid.uuid4()); exp=(datetime.now(timezone.utc)+timedelta(seconds=lock_seconds)).isoformat()
            db.execute("UPDATE tasks SET status='RUNNING',task_version=task_version+1,lease_token=?,lease_owner=?,lock_expires_at=? WHERE run_id=? AND status=? AND task_version=?",
                       (token,worker,exp,rid,status,ver))
            if db.execute("SELECT changes()").fetchone()[0]!=1: return None
            return {"run_id":rid,"_lease_token":token,"task_version":ver+1}
    def renew_lease(self,rid,token,worker,extend_seconds=30):
        with self.tx() as db:
            row=db.execute("SELECT status,lease_token,lease_owner,lock_expires_at FROM tasks WHERE run_id=?",(rid,)).fetchone()
            if not row: raise OwnershipError("missing task")
            status,cur,owner,exp=row
            if status!="RUNNING" or cur!=token or owner!=worker or not exp or exp<=now(): raise OwnershipError("lease invalid or expired")
            new=(datetime.now(timezone.utc)+timedelta(seconds=extend_seconds)).isoformat()
            db.execute("UPDATE tasks SET lock_expires_at=? WHERE run_id=? AND lease_token=?",(new,rid,token))
    def request_approval(self,rid,scope,ttl_seconds=3600):
        with self.tx() as db:
            row=db.execute("SELECT task_version FROM tasks WHERE run_id=?",(rid,)).fetchone()
            if not row: raise ApprovalError("missing task")
            aid=str(uuid.uuid4()); exp=(datetime.now(timezone.utc)+timedelta(seconds=ttl_seconds)).isoformat()
            db.execute("INSERT INTO approvals VALUES(?,?,?,?,?,?,?)",(aid,rid,row[0],scope,None,exp,None)); return aid
    def decide_approval(self,aid,decision):
        if decision not in ("approved","denied"): raise ApprovalError("bad decision")
        with self.tx() as db:
            row=db.execute("SELECT decision FROM approvals WHERE approval_id=?",(aid,)).fetchone()
            if not row or row[0] is not None: raise ApprovalError("missing or already decided")
            db.execute("UPDATE approvals SET decision=? WHERE approval_id=?",(decision,aid))
    def authorize_operation(self,rid,op_key,scope,lease_token,worker):
        with self.tx() as db:
            t=db.execute("SELECT status,lease_token,lease_owner,task_version,approval_required FROM tasks WHERE run_id=?",(rid,)).fetchone()
            if not t or t[0]!="RUNNING" or t[1]!=lease_token or t[2]!=worker: raise OwnershipError("not owner")
            if not t[4]: raise ApprovalError("approval path misuse")
            existing=db.execute("SELECT run_id,scope FROM operations WHERE operation_key=?",(op_key,)).fetchone()
            if existing and existing!=(rid,scope): raise ApprovalError("operation key rebound")
            a=db.execute("SELECT approval_id FROM approvals WHERE run_id=? AND task_version=? AND scope=? AND decision='approved' AND consumed_at IS NULL AND expires_at>?",(rid,t[3],scope,now())).fetchone()
            if not a: raise ApprovalError("no valid approval")
            db.execute("UPDATE approvals SET consumed_at=? WHERE approval_id=?",(now(),a[0]))
            token=str(uuid.uuid4())
            db.execute("INSERT INTO operations(operation_key,run_id,scope,auth_token,state,created_at) VALUES(?,?,?,?,?,?)",(op_key,rid,scope,token,"authorized",now()))
            self.audit(db,"operation_authorized",rid,op_key); return token
    def record_intent(self,rid,op_key,auth_token):
        with self.tx() as db:
            row=db.execute("SELECT run_id,auth_token,state FROM operations WHERE operation_key=?",(op_key,)).fetchone()
            if not row or row!=(rid,auth_token,"authorized"): raise ApprovalError("missing authorization")
            db.execute("UPDATE operations SET state='intended' WHERE operation_key=?",(op_key,))
    def mark_executed(self,op_key):
        with self.tx() as db:
            row=db.execute("SELECT state FROM operations WHERE operation_key=?",(op_key,)).fetchone()
            if not row: raise ApprovalError("unknown operation")
            db.execute("UPDATE operations SET state='executed' WHERE operation_key=?",(op_key,))
            db.execute("INSERT INTO execution_log(operation_key,ts) VALUES(?,?)",(op_key,now()))
    def recover_orphans(self):
        with self.tx() as db:
            rows=[r[0] for r in db.execute("SELECT run_id FROM tasks WHERE status='RUNNING' AND lock_expires_at<?",(now(),)).fetchall()]
            for rid in rows:
                db.execute("UPDATE tasks SET status='PENDING',task_version=task_version+1,lease_token=NULL,lease_owner=NULL,lock_expires_at=NULL,retry_count=retry_count+1 WHERE run_id=? AND status='RUNNING'",(rid,))
            return rows
    def operation_state(self,op_key):
        db=sqlite3.connect(self.path); row=db.execute("SELECT state FROM operations WHERE operation_key=?",(op_key,)).fetchone(); db.close(); return row[0] if row else None
    def metrics(self):
        db=sqlite3.connect(self.path)
        dup=db.execute("SELECT COUNT(*) FROM (SELECT operation_key,COUNT(*) n FROM execution_log GROUP BY operation_key HAVING n>1)").fetchone()[0]
        pending=db.execute("SELECT COUNT(*) FROM tasks WHERE status='PENDING'").fetchone()[0]
        db.close(); return {"duplicate_execution_count":dup,"pending":pending}
