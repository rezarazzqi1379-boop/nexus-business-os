# NEXUS PLO Cloud Execution Substrate v0.3

Linux/Docker-native durable execution substrate for NEXUS. It removes Windows from the critical path while remaining a shadow/CI-tested component rather than a second source of truth or a production authorization system.

## Canonical ownership boundary
- PR #4 / PR #37 own consequential exact-action approval semantics.
- PR #16 owns Supabase least-privilege / ACL / RLS hardening.
- PLO owns durable task/run state, leases/fencing, crash/orphan recovery, operation intent/execution journal, duplicate-execution telemetry, provider reconciliation state, and Linux/PostgreSQL runtime mechanics.
- Compatibility approval fixtures in this isolated runtime are test scaffolding only; production authorization must consume the canonical Core gate rather than create a second authority.

## Verified safety state
- Gmail/search adapter: READ-ONLY.
- Gmail send/draft/modify: hard-disabled.
- Uncertain provider reconciliation is HOLD, never blind resend.
- Expired leases cannot renew, authorize, or cross the authorize -> intent gap.
- `executed` cannot be recorded before `intended`.
- Stale task-version approvals fail closed.
- Expired RUNNING tasks are recoverable and old workers remain fenced.
- Duplicate logical execution is measured from an append-only execution log.
- PostgreSQL two-worker claim isolation is tested with row locking / `SKIP LOCKED`.
- Worker backend selection is explicit/observable: `auto`, `sqlite`, or `postgres`.
- Runtime PostgreSQL worker does **not** perform DDL migrations; migration/provisioning is a separate deployment concern so the runtime role can remain least-privileged.

## Local / CI usage
```bash
python tests/test_cloud.py

# SQLite local fallback
python worker.py --backend sqlite --db ./data/nexus_plo.db

# PostgreSQL requires a separately provisioned/migrated schema
export NEXUS_PLO_DATABASE_URL='postgresql://...'
python tests/test_postgres.py
python worker.py --backend postgres

docker build -t nexus-plo-cloud:v0.3 .
docker run --rm -v "$PWD/data:/data" nexus-plo-cloud:v0.3
```

## Production gate
Current maturity is **Implemented + CI-tested in isolated/shadow runtime**. It is not merged, not deployed, and not production-authorized. Before production promotion: use a dedicated least-privilege runtime DB role, isolate PLO state from canonical business tables, separately provision schema/migrations, verify Supabase/hosted PostgreSQL compatibility, run hosted restart/crash tests, and collect live telemetry.

GitHub Actions is CI/reproducibility, not durable storage. A persistent volume or server PostgreSQL backend is required for durable hosted runtime state.
