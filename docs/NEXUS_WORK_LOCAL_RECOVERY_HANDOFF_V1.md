# NEXUS Work Handoff: Local Recovery and Platform Trial

State: DRAFT / NOT RUN ON WINDOWS.
Repository expected: C:\Users\AvallPc\nexus-business-os
Reported active local branch: research/china-sourcing-v0.1
Reported local HEAD: fea723a5d2472cbef6b8e562185fcaa89d924f3
Remote spelling requires readback from local git: rezarazzaqi1379-boop versus GitHub connector rezarazzqi1379-boop.
Do not assume these refer to the same accessible remote without independent verification.

## Read-only phase

1. Capture git status --porcelain=v1 -uall, branch -vv, for-each-ref, remote -v, worktree list, rev-parse HEAD and current branch.
2. Record inventory hashes and paths of modified/untracked files without printing secrets or ingesting credentials.
3. Check existing local refs and compare with GitHub API; do not fetch --prune before preserving ref inventory.
4. Verify Python, Node, Docker, RAM, disk, available ports and local permissions.
5. Run safe non-mutating tests only after identifying their side effects; prefer isolated copy or disposable worktree outside dirty repository.
6. Classify each branch by unique commits, verified tests, canonical source relevance and merge readiness.

## Platform sandbox

1. Verify source, release commit, license, security and dependency footprint for Twenty and EspoCRM.
2. Choose one after comparison; use an isolated local NEXUS-LAB directory and synthetic data only.
3. Record installation commands, health endpoint, round-trip CRUD, auth denial, restart persistence, resource metrics, uninstall and rollback.
4. Never connect company Gmail, CRM, bank or customer data during sandbox.
5. Do not install agents, hooks or services into the dirty local repository.

## Stop conditions

Any unexpected local modification, secrets exposure, nonzero spend, production write, destructive action, network access to unapproved destination or inability to verify source requires stop and review.

## Reporting

Per operation: evidence source, timestamp, commit, maturity state (DESIGNED/IMPLEMENTED/TESTED/DEPLOYED), results, failures, unknowns, rollback, exact approval needed.
