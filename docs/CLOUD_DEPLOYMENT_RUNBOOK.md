# NEXUS cloud deployment runbook

## Required platform setup

1. Create a private Git repository and push this directory.
2. Create a Railway service from that repository. The included Dockerfile and
   `railway.toml` are the source of truth.
3. Attach a persistent volume mounted at `/data`.
4. Generate a secret locally, for example `openssl rand -hex 32`, and store it
   as `NEXUS_ACCESS_TOKEN`. Do not commit it.
5. Keep `NEXUS_AUTH_REQUIRED=1`; set the health check to `/ready`.
6. Deploy, then verify `/health`, `/ready`, authenticated `/console`,
   `/v1/system/diagnostics`, `/v1/canonical/status`, and
   `/v1/workflows/hydrostatic-audit`.

`OPENAI_API_KEY` is optional. Add it only after billing and a project budget are
configured. Absence of that key does not prevent deterministic operation.

## Acceptance checks

- `/ready` returns 200 and only a coarse status.
- protected endpoints return 401 without credentials and 200 with credentials.
- canonical status lists exactly six bundled source documents.
- hydrostatic audit returns four evidence hold points and
  `external_action_authorized=false`.
- a backup verifies successfully after creation.
- the complete automated test suite passes.

## Backup and recovery

Run the backup function on a schedule and copy the resulting archive and SHA-256
manifest to encrypted storage outside the Railway volume. Test restoration on a
separate service before treating the backup as recoverable. Never expose backup
files through the web application.

The included recovery command refuses to overwrite a non-empty target:

```bash
python ops.py restore-backup /path/to/nexus-backup-TIMESTAMP \
  --destination /empty/recovery-directory
```

## Security operations

- Railway HTTPS must remain enabled; rotate the access token after suspected
  exposure and at operating-policy intervals.
- Restrict repository and deployment access with MFA and least privilege.
- Keep external connectors read-only until their isolated pilot passes.
- Add edge rate limiting before Internet-wide exposure.
- Review logs without recording authorization headers, source documents or
  secrets.

## Rollback

Retain the last known-good container image and a verified pre-deployment backup.
On failure, stop traffic, restore both SQLite databases and the vault from one
consistent backup set, deploy the prior image, then run all acceptance checks.
