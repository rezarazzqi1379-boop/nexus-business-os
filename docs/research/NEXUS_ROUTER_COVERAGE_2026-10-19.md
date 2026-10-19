# Router coverage review — 2026-10-19

Local development only. The previously uncommitted CLI now defaults to one worker;
explicit worker selection remains supported. Snapshots disclose their 300-row cap,
project/action task totals, project event totals and truncation flags.

Independent verification: 1712 tests passed with one upstream Starlette warning.
Source hashes and exact command are recorded in data/research/continue-review-20261019.json.
That record describes the pre-commit working tree; it is not remote CI evidence.
Two additional negative tests cover foreign project/action exclusion and event
truncation without including foreign events. No external service is required.

The old development worktree lacks newer contracts present in 8cdc. This remains
recorded drift, not permission to silently merge branches or promote authority.
Registry/Master HOLD and Secret Guard remain unchanged. No model download,
installation, paid request, push, merge, deployment or permission expansion occurred.

Rollback: revert this focused commit on the development branch. Do not reset
unrelated worktrees. Promotion awaits branch reconciliation and exact approval.
