# NEXUS Unified-System Audit — 2026-09-12

## Implemented baseline

- Unified metadata/evidence index over existing authoritative stores.
- SQLite-consistent, staged local backups with per-file SHA-256 manifest.
- Secret-name and workspace-containment gates.
- Conversation need detection, token budgeting, and bounded idea proposals.
- Portfolio watchdog with visible running, queued, or waiting coverage for every registered project.
- One control-plane path from observed need to scheduled reversible work.

## Current activation evidence

- Ten existing data assets registered.
- Eight of eight registry projects covered by the watchdog.
- Initial snapshot `initial-unified-20260912` created and verified locally.
- External actions remain disabled.

## Remaining weaknesses

1. The hub is an index, not yet the sole operational database. Existing stores remain separate authorities.
2. ChatGPT task content is not continuously imported; only authorized metadata/export adapters can feed it.
3. Snapshot manifests detect corruption but are not authenticated with an external HMAC/signing key.
4. Restore is intentionally not automatic. It needs manifest-only payload selection, application-schema checks, staging, and explicit cutover.
5. Existing `ops.py` backup/restore has a different legacy path and must not be treated as equivalent to `BackupManager`.
6. The full test suite has Windows/Python 3.14 cleanup failures because several legacy SQLite connections are not explicitly closed.
7. Portfolio pulses are not yet persisted from actual task outcomes, so the first watchdog cycle marks every project as needing refresh.
8. Research evidence models still need a common provenance envelope and cross-run identity/deduplication.
9. Live web providers still require egress/SSRF controls, timeout, rate limit, credential isolation, and auditable provenance.
10. Automatic recurring execution has not been enabled; scheduling cadence and notification policy need an explicit operational choice.

## Predicted next constraints

- Data volume will make full-copy backups inefficient; content-addressed immutable artifacts and incremental retention will be needed.
- Multiple workers will require fencing tokens, atomic budget reservations, and circuit-breaker enforcement during dispatch.
- Cross-project entities will need stable global identities plus project-specific bindings and merge/split history.
- As automation grows, evidence freshness and approval queues—not model capability—will become the main throughput constraints.

## Next safe build order

1. Central connection factory and explicit close migration for legacy SQLite stores.
2. Persist real task/project pulses and outcome trajectories into `nexus.db`.
3. Read-only ChatGPT export/task metadata importer with idempotent digests.
4. Authenticated backup manifest and manifest-only staged restore verifier.
5. Common provenance envelope and unified read query API.
6. Recurring watchdog automation after cadence and notification policy are confirmed.
