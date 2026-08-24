# Verification report — 2026-08-24

## Result

Release candidate accepted for a private cloud pilot.

- Automated suite: 136 tests passed, 0 failed.
- Real Uvicorn process: `/health` 200, `/ready` 200.
- Access control: unauthenticated `/console` 401.
- Protected diagnostics: auth, state database, canonical database and vault all ready.
- Canonical ingest: 6 documents, idempotent and digest-bound.
- Hydrostatic audit: 4 evidence hold points; external action authorization false.
- Backup and recovery: consistent SQLite/vault set, SHA-256 verification,
  tamper rejection, safe-archive checks and a successful full restore rehearsal.

## Security review and fixes

The review found and the release fixes: fail-open authentication defaults,
unbounded request bodies, expensive public readiness checks, DOCX decompression
resource exhaustion, same-ID concurrent vault collisions, early-response header
gaps and unknown-project event pollution. Security regression tests cover these
boundaries.

The second critical review added a fail-closed recovery tool. It refuses a
tampered backup, unsafe archive members and any non-empty restore destination,
then rechecks SQLite integrity after restoration.

Residual deployment controls: enable platform HTTPS, edge rate limiting, MFA,
least-privilege repository access and encrypted off-volume backups. A public
Internet launch should not precede those platform controls.

## Environment limitation

The container image was not built in this execution environment because no
Docker or Podman executable was installed. The same application was exercised
as a real Uvicorn HTTP process, and the Dockerfile is configured for a non-root
user, persistent `/data`, authentication and health checking. The hosting
platform must perform the final image build during deployment.
