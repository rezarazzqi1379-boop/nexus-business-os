# NEXUS PLO Cloud Runtime v0.2.1

Linux/Docker-native continuation of the verified PLO safety work. It removes Windows from the critical path.

## Safety state
- Gmail/search adapter: READ-ONLY.
- Gmail send/draft/modify: hard-disabled.
- Approval is consumed before an approval-required side effect can be recorded.
- Approval is bound to exact task version and scope.
- Expired leases cannot be resurrected.
- Expired RUNNING tasks are recoverable.
- Duplicate logical execution is measured from an append-only execution log.
- Uncertain Gmail reconciliation is HOLD, never blind resend.

## Run
```bash
python tests/test_cloud.py
python worker.py --db ./data/nexus_plo.db
docker build -t nexus-plo-cloud:v0.2.1 .
docker run --rm -v "$PWD/data:/data" nexus-plo-cloud:v0.2.1
```

GitHub Actions is CI/reproducibility, not durable storage. A persistent volume or server database is required for durable runtime state.
