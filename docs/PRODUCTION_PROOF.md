# NEXUS Production Proof v1

`production_probe.py` is a read-only post-deployment verification contract. It
checks the public boundary without receiving or storing credentials.

## Checks

- `/health` is alive and reports `status=ok`;
- `/ready` is ready and reports `status=ready`;
- `/login` serves the expected NEXUS login form;
- browser access to `/console` redirects to `/login?next=/console`;
- an unauthenticated API request remains blocked with `401`;
- every response retains the required security headers.

## Run

```bash
python production_probe.py https://nexus-business-os-production.up.railway.app \
  --output production-proof.json
```

Exit code `0` means every check passed. Exit code `2` means at least one check
failed. The JSON output includes response-body hashes, not response bodies or
credentials.

## Trust boundary

This proves the unauthenticated production boundary only. Successful owner
login still requires a separate human check because the access token must not
be transmitted to CI, logs, command arguments, reports or chat.

The probe rejects non-HTTPS targets, embedded credentials, URL queries or
fragments, localhost and non-global IP targets. It does not deploy, write to the
service, rotate secrets or authorize an external action.
