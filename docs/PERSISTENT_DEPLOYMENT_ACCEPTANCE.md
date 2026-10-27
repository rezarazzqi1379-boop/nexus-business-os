# Post-merge runtime and persistent-container handoff

Stage: STABILIZE / prepare DEPLOY. Operator: repository owner. No production
deployment, host purchase, credential provisioning, email or authority promotion.

## Verified acceptance on the prepared configuration

PR #117 implementation `017406114322f69edf2f08c643a604e8ebae9127` passed the
actual Linux Docker workflow **40557056463** (job **122375809416**): auth,
readiness, UID 10001 API process, named-volume restart persistence, atomic queue
checkpoint/supervisor, replay with zero reads, verified backup manifest, restore
of root SQLite stores/vault into an empty target, overwrite refusal and disposal
of the test resources. The registered hub snapshot's manifest was verified
separately; this does not claim a complete production-hub disaster recovery drill.
Regression CI **40557056458** passed: 680 unittest, 661 pytest tests/ and 14
failure-derived checks (overlapping suites). Final local tests/ + evals/:
**1737 passed**, one existing warning, 79.02 seconds; focused correction suite:
**70 passed**, 14.07 seconds. No application runtime code was changed.

Initial container runs **40553727248** and **40556549708** failed in startup/
readiness, despite successful image builds. The probe's transient loopback-reset
handling was reproduced locally (2 failed / 1 passed), then fixed with bounded
retry for RemoteDisconnected/ConnectionResetError. HTTP 200 remains mandatory;
the negative readiness fixture still exhausts the bound and fails. The succeeding
container run provides acceptance evidence after this correction, not a claim
that the failed runs succeeded. Diagnostics export only fixed categories.

Evidence: `data/research/postmerge-container-acceptance-20261027.json`.
Configuration is VERIFIED in a disposable CI container; production deployment
and off-host disaster recovery remain NOT_STARTED / approval-gated.

## Recovered operating baseline

PR #116 is merged at main `45ced379e6aa2746dd2fe2f43915110bcf057a9e`.
Main runtime run **40494875577**, job **122157684417**, succeeded via manual
dispatch. Its real public research summary says REAL_PUBLIC_HTTP, one verified
task, two GETs, accepted supervisor, checkpoint integrity and suppressed replay.
Main regression run **40494431196**, job **122156168254**, also succeeded.
This verifies a main-branch run, not guaranteed future scheduler delivery.
Existing weekday schedule, bounded transport, queue and supervisor are unchanged.
No reproducible research-runtime defect was found in this review.

Focused baseline command:
`python -m pytest -q tests/test_free_research.py tests/test_public_research_agent.py tests/test_router_runtime.py tests/test_router_console.py tests/test_execution_durability.py evals/test_cloud_hardening.py`
Result: **79 passed**, one existing Starlette warning, 18.48 seconds.

## Vercel 404 diagnosis

The provider's project/deployment tree contains only `src/index.html`. The
retrieved file is a static page saying `Runtime bootstrap checkpoint.`; it
contains no Python API. A new unauthenticated probe found `/` returns 200 with
that marker, while `/health`, `/ready` and `/v1/system/diagnostics` return 404.
Provider READY therefore refers to the placeholder. No deployed Git revision
was returned. See `data/research/postmerge-vercel-20261027.json`.

Do not add redirects to disguise these 404s or move SQLite into an ephemeral
function. The existing managed-container/Railway target is retained as an
option; no Vercel release or protection/share-link change is authorized here.

## Smallest persistent configuration

`deploy/compose.persistent.yml` runs the existing Dockerfile image on a named
Linux Docker host with a named `/data` volume. It requires an explicitly reviewed
image and externally supplied token, disables implicit image pulls, keeps auth
on, binds the HTTP port to loopback, limits resources, uses a read-only image
filesystem and a bounded temporary filesystem. One API process is retained.

The existing Railway Dockerfile and railway.toml remain available; Railway still
requires a separately provisioned persistent volume at `/data`. Do not create a
paid service/volume until the owner approves the exact host/account and cost cap.

Set NEXUS_IMAGE to a reviewed image (prefer an immutable digest already loaded
on the target), supply a randomly generated >=32-character NEXUS_ACCESS_TOKEN
through the host's approved secret mechanism, and keep it out of the repository.
With that separate target authorization, validate without printing secrets:

```sh
docker compose -f deploy/compose.persistent.yml -p nexus-persistent config --quiet
docker compose -f deploy/compose.persistent.yml -p nexus-persistent up -d --no-build
```

Do not use `compose config` without `--quiet` in logs: resolved environment values
can include the token. Required-value interpolation follows the official
[Docker Compose interpolation contract](https://docs.docker.com/reference/compose-file/interpolation/).
An approved HTTPS reverse proxy, firewall, operator access and token rotation
must be ready before exposing the API beyond localhost.

The API service stores state.db, canonical.db and nexus_vault on `/data`.
Any separately approved persistent worker must also place its queue/checkpoint
database and authoritative hub there. Do not share writable SQLite between
different hosts or attach the same production volume to competing deployments.
Existing fencing remains queue-scoped; a named volume is not a distributed lock.
Free-runtime research remains a separate batch workflow with disposable queues.

## Executable container acceptance

The new NEXUS Persistent Container Acceptance workflow builds the existing image
without pushing it or contacting a production host. It runs
`python scripts/verify_persistent_container.py --image <built-image>`.

The script creates a fresh random Compose project/volume and ephemeral auth token.
It rejects missing-token configuration, verifies readiness/health, unauthenticated
401 and authenticated 200, verifies the actual API process runs as UID 10001,
seeds a frozen queue fixture and checkpoint, restarts the container, and checks
the same volume's state/vault and duplicate replay without network reads. It
verifies a BackupManager manifest using the SQLite backup API and checks the
existing ops backup/restore against a separate empty scratch directory, including
refusal to overwrite it. Only fixed verification flags leave the container; no
DB, source body, secret or raw container log is published. Random test resources
are removed at the end. The workflow is bounded to 12 minutes and runs on relevant
PR changes or manual dispatch; it is not a deployment/scheduler service.

Queue fixtures in this container test are explicitly FROZEN_TEST_FIXTURE. Main
free-runtime logs supply independent live-public evidence. Local Docker is not
installed in this session: the local invocation correctly returned BLOCKED /
DOCKER_UNAVAILABLE. The Linux Actions result above is independent actual
container evidence, not a local execution claim.

## Backup and rollout gate

Treat host/volume loss separately from process restart. Register all required
stores in the existing UnifiedDataHub and use BackupManager for approved local
snapshots; its SQLite backup API handles WAL consistency. Mark secret assets and
exclude .env files, credentials and keys. Keep a verified copy outside the live
volume using a separately approved destination and encryption. Same-volume
snapshots alone do not provide disaster recovery. Schedule/copy permissions,
retention and operator restore ownership remain target-specific approval items.

Before promotion: pin the reviewed image and config, verify the named durable
volume, HTTPS/auth, real bounded task, lease recovery, restart, disk-full policy,
manifest integrity and restoration into an empty staging target. Retain the
previous image and matching verified snapshot. Rollback must explicitly select
image and restore target; never overwrite live storage or run `down --volumes`
on the production project. This destructive flag is used only by the uniquely
named disposable acceptance project.

Production remains BLOCKED pending the exact target, financial authorization if
needed, protected secrets/environment approval, independent durable-storage and
off-volume recovery evidence, and the existing consequential authority HOLD.
