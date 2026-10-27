# Bounded GitHub Actions operation

Owner/operator: repository owner. Scope: PRJ-NEXUS-SANDBOX, public read-only
engineering research. Authority HOLD is unchanged. No email, paid model call,
commercial transaction, account onboarding or production-state promotion.

## Run and verify

The existing NEXUS Free Runtime workflow keeps its weekday schedule and manual
dispatch. Changes to its runtime files also run it on pull requests. It retains
startup/readiness/health/unauthenticated-diagnostics smoke checks and additionally
checks authenticated diagnostics. Then it runs:

```sh
timeout 60s python nexus_free_research.py --summary "$RUNNER_TEMP/public-research-summary.json"
```

The fixed PublicResearchRuntime task submits through the existing coordination
plan, queue, owner/attempt/expiry fences, atomic checkpoint and supervisor. It
reads only the official openai/openai-agents-python repository and latest-release
API URLs, unauthenticated. Two GET attempts maximum, 64 KiB per response, existing
transport deadlines, no redirects, no model or paid provider. The workflow has a
12-minute job bound and a two-minute research-step bound; the command has a
60-second wall-clock bound. One failed acquisition blocks the run, emits a fixed
redacted reason and does not count a verified task. No synthetic fallback.

A green run must contain both the original smoke PASS and a REAL_PUBLIC_HTTP
summary with one completed task, two reads, accepted supervisor, verified
checkpoint digests and suppressed replay. A reopened queue must reject duplicate
submission and perform no additional GET. Frozen tests are explicitly labelled
FROZEN_TEST_FIXTURE; they never prove live source availability.

Only public fixed URLs, source SHA-256 digests, task counters and verification
flags are printed/exported. The sole artifact is public-research-summary.json,
retained three days. Full response bodies, raw SQLite/checkpoint contents, vault,
secrets and internal paths are not artifacts. Checkout credentials are not
persisted. Workflow token scope stays contents:read.

## Reliability and limits

Public GitHub rate limits, network outages, quotas and scheduler delays can fail
or postpone this job; a red run is not silently converted into success. Review
the fixed summary reason and retry manually only when appropriate. No automatic
unbounded retry or paid fallback is enabled.

Each run uses a fresh disposable queue. Duplicate protection and restart checks
are within that queue/run, **not** a cross-run exactly-once guarantee. A rerun or
later scheduled run intentionally makes a new observation. GitHub concurrency
serializes this workflow's runs. Queues/checkpoints disappear at job termination.
The API process is killed at smoke-step exit. GitHub Actions is a bounded batch
execution environment, not an always-on production server. Account quotas apply;
zero additional hosting cost does not imply unlimited execution minutes.

Real-source results are CLAIM evidence, not corroborated commercial facts or
canonical authority. This deterministic worker is not an LLM reasoning agent.
Use the existing authenticated authority gate for consequential project decisions.

## Independently assessed deployment

Baseline run 40478369970 at b46856ea92eb981ddb0dea9f885d740c73418bd9 was independently
confirmed successful, including startup and auth smoke (job 122102152873).
The existing Vercel deployment dpl_34W7YryHDSp5z2UM6yUzy1hp74K3 is reported READY
and LAMBDAS by the provider, but public /health, /ready and /v1/system/diagnostics
all returned 404 during this assessment. No deployed Git SHA was returned. Its
NEXUS runtime and persistent SQLite storage are therefore not verified. No Vercel
configuration was changed and no temporary share/protection bypass was created.

## Permanent service acceptance (separate approval and verification)

Retain the existing Dockerfile/Railway architecture rather than moving SQLite
to ephemeral functions. Before production deployment, verify the named target,
protected-environment approval, account quota/price, private persistent /data
volume, non-root runtime ownership, authenticated HTTPS, generated secret stored
by the provider, /ready health check and recovery operator. Keep all state/vault
paths on that volume and all authority/commercial holds intact.

Pin the image to its reviewed commit; first test health/readiness, unauthenticated
401 and authenticated 200, read-only research, restart persistence, lease recovery
and two-worker fencing in staging. Use BackupManager/SQLite backup API, verify
manifest hashes and prove restore into a separate empty directory. Retain the
last tested image and matching verified snapshot; rollback must select explicit
targets and must never overwrite live data implicitly. No permanent target,
secret provisioning, persistent volume, migration or production rollout is
activated by this batch-runtime change.
