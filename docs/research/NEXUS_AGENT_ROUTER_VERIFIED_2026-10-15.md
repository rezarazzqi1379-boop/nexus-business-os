# Agent Router: independently executed synthetic foundation

## Recovery and authority

Baseline: `7b4c899668fdc461dc2974bebf191df000ecf9bb`, refreshed remote
`nexus/agent-router-pilot-2026-10-14`. Worktree:
`C:/Users/AvallPc/.codex/worktrees/agent-router-verification/nexus-business-os`.
Development branch: `codex/agent-router-verification-2026-10-15`.
Existing work in the continuity and Decision Gate worktrees was preserved.
GitHub PR #113 independently refreshed: OPEN, DRAFT, NOT MERGED, head
`db94bc73ac9cc9cb5c3b6df8437e546457114195`; that commit is an ancestor
of the pilot. Historical CI is not this new branch's CI. New remote CI NOT_RUN.
Registry/Master version/hash/supersession and real steel project authority remain
unresolved. Missing-authority bootstrap evidence is preserved from #113; a fresh
missing-authority preflight is recorded alongside this report. Sandbox allowance
is an explicit local synthetic mode, never a substitute for accepted authority.

## Architecture and implementation

`project_control_plane.WorkRequest` → qualified catalog recommendation and existing
scheduler → fixed synthetic adapter → existing `AutonomyStore.work_items` → three
bounded worker roles → atomic checkpoint + completion → existing `Supervisor`.
The journal and emergency-stop flag are tables in the SAME configured queue DB;
no new provider, framework, credential store or competing approval system.

Each persisted child has project/task/thread, lane/risk, role, catalog provenance,
bounded retry budget and lease ownership. All required capabilities must match.
The bridge default lane is now `engineering`, an actual scheduler-supported value.
Queue claims can be filtered by project AND action without breaking existing callers.
Submission/journal/three children commit atomically. Conflicting duplicate task
payloads are rejected; exact replay creates no work. Attempt-fenced renewal and
completion reject expired owners, including a reused worker name after restart.
Expired final attempts become dead letters. Retry allowance is split equally
between three roles and never exceeds the submitted attempt-unit budget.
Checkpoint and completion commit together; restart only claims remaining children.
Audit records are application-append-only, not cryptographically tamper-proof.
Stop/cancel prevent result commits; already-running synthetic Python cannot be
forcibly preempted. There are no external effects to compensate or repeat.

The catalog is a recommendation, not evidence an SDK/connector is installed or
healthy. The actual executor is fixed standard-library synthetic code. No network,
shell, arbitrary worker registration or credential lookup exists in the adapter.
Real provider health, model routing, reliability/cost/latency optimization remain
BLOCKED/NOT IMPLEMENTED. Deterministic local fallback is the one-worker mode;
the measured small workload favors it. Three roles are synthetic functions, not
three independently reasoning LLMs or a commercial source reconciliation engine.

## Independently executed commands and environment

Python `C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`, 3.14.7,
Windows 11 build 26100; pytest 8.4.2, fastapi 0.141.1, httpx 0.28.1.
Use `PYTHONPATH=src`; no dependencies installed.

1. `git fetch origin` (initial sandbox FETCH_HEAD write denied; authorized
   escalation succeeded). Checked branch/remotes/worktrees/ancestry and PR #113.
2. `python -m unittest tests/test_agent_router_pilot.py tests/test_agent_router_bridge.py`:
   baseline **8 passed / 1 error** (`invalid_execution_lane`); after repair **9 passed**.
3. `python -m pytest -q -p no:cacheprovider --basetemp <writable-root>/data/research/pytest-router-focused3 tests/test_agent_router_pilot.py tests/test_agent_router_bridge.py tests/test_router_runtime.py tests/test_router_console.py`:
   **32 passed**, one upstream Starlette/httpx deprecation warning.
4. Full initial `python -m pytest -q -p no:cacheprovider --basetemp <writable-root>/data/research/pytest-router-full tests evals`:
   **1657 passed / 1 failed**. Windows deletion exposed unclosed SQLite connections
   in API startup readiness. Explicitly close those connections; do not weaken
   security assertions. Focused runtime + console + cloud hardening: **34 passed**.
5. Final full rerun and exact log/hash: see `agent-router-verification-2026-10-15.json`.
6. `python benchmark_agent_router.py --output data/research/agent-router-benchmark-2026-10-15.json`:
   ten sequential + ten concurrent runs, real queue transactions, no injected sleeps.
7. `git diff --check`; in-memory compilation of changed Python files.

Initial console test assumed a redirect; existing middleware correctly returns
401 for this path. Corrected the assertion. UI uses an external same-origin script
to comply with existing CSP; status is rendered with textContent. Temporary sandbox
and memory-lock permission failures were resolved with scoped local execution;
no OS permission changes. The branch lacks `agent_reach_preflight`; local-only
acquisition decision was exercised in the continuity checkout that contains it.

## Benchmark and failure gates

Measured medians: one worker **0.066811 s**, three workers **0.095651 s**;
sequential/concurrent ratio **0.698489**. Concurrency is about 43% slower for this
tiny SQLite-heavy workload; do not advertise speedup. In all 20 repetitions:
completion 100%, evidence completeness 100%, errors/retries/replay executions 0,
supervisor accepted the complete synthetic packet. CPU seconds and peak traced
Python heap per repetition are in the JSON; heap is not whole-process RSS.
Model calls/tokens and API cost are zero in this workload. Total Codex session
token consumption is UNKNOWN. Token allocator executed with reserves:
history 1000 / evidence 2500 / working 7000 / output 1500. These are allocations,
not measured consumption or context enforcement by the desktop app.

Tests cover cross-project/action claims, unauthorized/forged approval/missing
authority scope, duplicate conflict/concurrent submission, stale attempt/expired
renewal, process death after claim, partial checkpoint restart, killed-transaction
rollback, retry-budget exhaustion, cancel/stop, missing connector/capability,
malformed evidence, replay and authenticated read-only console.
Existing full regression covers canonical ApprovalStore single-use exact-scope
approval and project-memory concurrency from #113. No external approval consumed.

## Runtime and console recovery

Local development commands (explicit disposable queue path):

```powershell
$env:PYTHONPATH = 'src'
& 'C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe' nexus_router_runtime.py --db C:/temp/nexus-router-test.db --submit proof_001 --drain --workers 1
# A new process can resume the SAME queue; omit --submit to drain remaining work.
& 'C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe' nexus_router_runtime.py --db C:/temp/nexus-router-test.db --drain --workers 1
```

Use an existing sandbox queue path to share AutonomyStore; this never points at
production automatically. Console: set `NEXUS_ROUTER_SANDBOX_DB` to that queue
before starting the EXISTING authenticated API through its normal local launcher.
`/console/router` shows task status/owners/leases, checkpoint evidence, bounded
history, costs and denied-external approval policy. `/v1/console/router` is a
read-only API; missing configuration returns NOT_CONFIGURED. Neither GET creates
tables or work. No submit/approve/execute HTTP endpoint was added. The frontend
shares existing authentication; frontend access grants no execution authority.

Independent subprocess completion, forced process death and fresh-process replay
were executed. This is a restartable CLI, not an installed daemon, scheduled
service or production deployment. No claim of 24/7 persistence or real browser
render verification. POSIX, network filesystems and power-loss durability untested.

## Controlled improvement, security and rollback

Existing `self_improvement_runtime` is the evaluation interface. This run is PARTIAL
for learning because corrections and missing live authority remain; no promotion.
Candidate v1: choose sequential fallback for this small local workload. Baseline:
paired benchmark JSON. Expected benefit: less queue/thread overhead. Scope:
synthetic only. Cost: zero provider cost. Security: fixed executor, exact-project
SQL and attempt fencing; no external actions. Decision: EXPERIMENT_ONLY. Version:
this development commit. Rollback: pass `--workers 1`; do not edit production policy.

Rollback code by reverting this isolated commit, then run the same focused/full
tests. The additional router tables are inert to old code; preserve the database
and journal. Do not delete or restore production state. No database down-migration
or external effects occurred. Memory checkpoint is historical evidence; supersede
it instead of deleting it. Registered installed NEXUS runtime was not upgraded.

Next milestone: review this bounded patch and exact-commit CI after exact publication
approval; resolve canonical authority; then design authenticated runtime identity,
fresh provider health and real reconciliation evaluations before external workers.
No push, merge, deploy, account, permission change or paid install performed.
