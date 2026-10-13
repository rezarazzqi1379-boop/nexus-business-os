# NEXUS Local-First / Cloud-Ready Runbook v1

Status: PREPARED, NOT INSTALLED. Windows 11 pilot first, cloud later.
No auto-start, paid calls, external outreach, protected merge or deployment.

## Read-only local preflight

In PowerShell, run from your own Windows account:

```powershell
$repo = 'C:\Users\AvallPc\nexus-business-os'
if (-not (Test-Path -LiteralPath $repo -PathType Container)) { throw 'Repository directory missing' }
git -C $repo rev-parse --is-inside-work-tree
git -C $repo branch --show-current
git -C $repo status --short
git -C $repo remote -v
git -C $repo rev-parse HEAD
py -V
python --version
git --version
```

Do not reset, clean, pull or checkout if uncommitted work exists. Compare local HEAD with GitHub exact-head CI before testing.

## Sandbox after preflight

Only with a clean/approved working tree and working Python:

```powershell
cd 'C:\Users\AvallPc\nexus-business-os'
python -m venv .venv-nexus
.\.venv-nexus\Scripts\python.exe -m pytest -q tests/test_nexus_simulation.py tests/test_nexus_budget_gate.py tests/test_platform_runner_contract.py
```

Installing pytest or any dependency requires a reviewed dependency lock and local approval; do not silently fetch packages. Python stdlib can compile the modules with `python -m compileall -q nexus_simulation.py nexus_budget_gate.py platform_runner_contract.py`.

## Cloud-ready portability

Retain source and fixtures in version control; keep credentials out of Git. Externalize secrets and environment configuration, use independent state snapshots, logs, backups, kill switch and an explicit host selection before deployment.

## Acceptance

1. Local path and Git validity confirmed.
2. Local HEAD/branch/status/remotes recorded.
3. Python and dependency versions recorded.
4. Deterministic simulation and budget tests passed on local host.
5. Evidence state read back and project boundaries validated.
6. No external action and no new spending.
7. Rollback: remove isolated virtual environment; never alter original user data.

Do not claim installation, always-on operation, global ChatGPT activation or cloud deployment until observed.
