# NEXUS execution verification — 2026-10-14

Scope: isolated local development, synthetic SANDBOX fixtures only. No production,
push, PR creation, publication, deployment, payment, contact or package installation.

## Recovery and authority

Read the requested [Work/Codex handoff](https://docs.google.com/document/d/1bJyokT1ORCn5agELPcOR2s7u0ddJeBdt6ihSsJb7uNI/edit),
modified 2026-10-14T11:12:42.969Z. Its status is HANDOFF PREPARED, NOT EXECUTED;
it is a work request/evidence pointer, not accepted canonical commercial authority.
Bounded connected Drive searches for NEXUS_Source_Registry_v1.8 and
NEXUS_Master_Context_v2.1 returned no results. This is a search coverage gap,
not proof that the documents do not exist. Accepted binaries/hashes, supersession
and steel business project ID remain unresolved. Actual bootstrap_chat run at
2026-10-14T17:53:43.668488+00:00 returned BLOCK with REQUIRED_AUTHORITY_MISSING for
authority.source_registry and authority.project_master. No commercial claim promoted.

Refreshed origin/main: `59f5fb386c023b1f04deaae15709c371e9bfd6d7`.
[Main CI 38383113740](https://github.com/rezarazzqi1379-boop/nexus-business-os/actions/runs/38383113740)
was independently refreshed and is successful at that exact SHA.
PR #111 observed head: `7543bce702a90924637c06741a52a6d4b38b94f7`, Draft/open.
[CI 38531225272](https://github.com/rezarazzqi1379-boop/nexus-business-os/actions/runs/38531225272)
is successful at that PR head; it does not certify these new local changes.

Created managed worktree `nexus-execution-verification/nexus-business-os` from
refreshed main, branch `codex/execution-verification-2026-10-14`. The earlier
worktree's uncommitted coordination changes were preserved. No bulk merge of
the buyer/Forge branches or alternate orchestration system was attempted.
Actual narrative state located at `.nexus/state/CURRENT_STATE.md`.

Existing memory bootstrap returned no recorded SANDBOX memory in this main-based
checkout. Existing allocator ran with history 1000, evidence 2500, working 7000,
output 1500 (12000 total). These are allocations, not measured consumption;
Codex session token consumption remains UNKNOWN. No model/API/provider eval calls.

## Existing code and measured failures

`execution_scheduler` selects priorities; it is not a durable worker. Durable
queue/claim/retry/lease state already exists in `autonomy.AutonomyStore` (SQLite).
`ApprovalStore` owns exact action digests and single-use consumption. Existing
supervisor and connector bootstrap provide acceptance and authority boundaries.
No new coordinator, queue, database, agent runtime or evaluation framework added.

Main baseline: 1584 passed, 35 failed, one upstream Starlette warning.
Failures: 34 Windows database cleanup failures from unclosed SQLite connections,
plus Git health interpreting successful-command stderr warnings as staged changes.
The earlier local mission baseline is separate: 2388 passed; its extra modules
are not all on current main. Counts across these branches are not directly comparable.

New durability baseline: 4 passed, 3 failed. Actual six-process memory writes
caused malformed JSON; supersede rewrote original namespace bytes; record lacked
an atomic-replacement crash boundary. Failures retained in evidence logs.

## Minimal fixes

- Existing project_memory: OS file lock plus in-process reentrant guard around
  read/modify/write; fsynced same-directory staging and atomic replacement.
  Namespace record bytes remain append-preserved; supersession events use an
  additive journal materialized by query. Legacy superseded_by fields still work.
  Cross-project/lane supersession is rejected. Lock and orphan staging files are
  local artifacts; orphan files are ignored, not treated as committed records.
- Existing audit/autonomy/canonical/state/backup SQLite paths explicitly close
  connections while preserving transaction commit/rollback contexts.
- Existing Git-health helper uses stdout on success and retains stderr on failure.
- Tampering test closes its own SQLite connection; no assertion was weakened.

Nine focused runtime tests exercise: six-process/150-record memory concurrency;
same-ID exclusion across instances; append-preserving supersession and isolation;
process exit before atomic commit and lock recovery; duplicate queue replay and
parallel claims; crashed worker lease recovery/stale-owner denial; concurrent
single-use approval and changed project/payload rejection; crash after a guarded
local effect without replaying it; missing Registry/Master fail-closed.

The local-effect test uses an exact fixture approval and a local file, never a
real outbound action. This demonstrates at-most-once guarded effect replay, not
exactly-once arbitrary external transactions. Crash between approval consumption
and effect execution can require manual reconciliation; this limitation remains.

## Commands and results

Interpreter: `C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`.
Actual versions: Python 3.14.7, pytest 8.4.2, FastAPI 0.141.1,
httpx 0.28.1, uvicorn 0.52.4. No dependency upgrade occurred.
Set PYTHONUTF8=1 and PYTHONPATH=src, cwd the isolated worktree.

```text
git fetch origin
git switch -c codex/execution-verification-2026-10-14
python -m pytest -q -p no:cacheprovider tests evals
python -m pytest -q -p no:cacheprovider tests/test_execution_durability.py
python -m pytest -q -p no:cacheprovider tests/test_execution_durability.py tests/test_project_memory.py tests/test_autonomy_queue_integration.py tests/test_autonomy_defer.py
```

After memory fix: 35 focused tests passed. After connection/Git-health fixes:
1626 passed / 1 failed; remaining failure was the tampering fixture's own open
connection. After closing it: 1627 passed. Subsequently added the guarded-effect
crash test: nine durability tests passed. Final full rerun saved in
`data/research/execute-final-2026-10-14.txt`.
Final run with all nine added durability cases: **1628 passed**, one pre-existing
Starlette deprecation warning, 65.71 seconds. Failure logs are retained as gzip
archives with raw SHA256/byte counts in execution-verification-measurements.json.
Compilation of eight changed sources in memory and git diff --check both pass.
This is local test verification; new-commit remote CI remains NOT_RUN.

An elevated-account attempt encountered pytest temporary-directory ACL errors
(108 passed, 1 failed, 38 setup errors). Reran with an explicit disposable basetemp
and normal sandbox permissions; this was an environment failure, not hidden test
success. compileall also encountered a pycache permission error; compiling the
eight changed runtime/test source files in memory succeeds without cache writes.
Environment lacks pip; dependency versions are read using importlib.metadata.

Promptfoo was not installed: pytest can directly exercise all requested OS/process,
lease, scope and approval invariants. No missing model/prompt evaluation capability
was demonstrated for this packet. Temporal/n8n/Prefect likewise unnecessary for
the already working durable queue tests.

## Limits, rollback and next action

Tested on Windows x64/Python 3.14; POSIX lock branch and sudden-power-loss behavior
remain unverified. Tests cover process crash/restart, not network filesystems or
distributed workers. Memory atomic replacement copies one namespace file and
fsyncs each mutation; large-store throughput was not benchmarked.

All concurrent memory writers must use this version's locking protocol; an old
reader ignores the new supersession journal. Do not mix deployed versions or
silently roll back a live store. No live memory format migration was performed.
Rollback for this isolated work: retain evidence, revert this local commit or
discard the isolated branch; original checkout and production remain untouched.

Next safe action: review the patch and portability; recover accepted authority
before any real steel qualification. Publishing this branch, PR creation, merge
and production rollout each remain outside this task's authorization.
