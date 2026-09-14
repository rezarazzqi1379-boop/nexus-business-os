# NEXUS Unified Data Environment

This directory is the local runtime home for the unified data index, portfolio
watchdog status, and verified backups.

- `nexus.db` indexes authoritative stores and evidence-linked observations.
- `portfolio_watch.json` records coverage across every registered project.
- `activation_status.json` records the last local activation result.
- `backups/<snapshot-id>/manifest.json` is the authority for each snapshot.

Runtime databases, status files, and backup payloads are intentionally ignored
by Git. Recreate or refresh the environment with:

```powershell
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe nexus_system_bootstrap.py --root .
```

Successful command output is not sufficient proof of backup. Verify the
snapshot with `BackupManager.verify_snapshot` before relying on it. Restoring
over live data is not automated and requires an explicit target and approval.
