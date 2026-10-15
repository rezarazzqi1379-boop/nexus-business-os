# NEXUS Railway Control Layer v0.1

Status: IMPLEMENTED ON FEATURE BRANCH / NOT PRODUCTION-ACTIVE

## Purpose

Give NEXUS a governed programmatic path to Railway without storing Railway credentials in the repository or treating deployment status as application-health proof.

Railway's Public API is GraphQL at `https://backboard.railway.com/graphql/v2`. Project tokens are scoped to one environment in one project and authenticate with the `Project-Access-Token` header. NEXUS prefers that narrower scope over an account token.

## Bootstrap boundary

One human bootstrap step remains required because this repository cannot create or read Railway credentials:

1. In the Railway project, create a **Project Token** for the Production environment.
2. Store the token as a GitHub Actions secret named `RAILWAY_PROJECT_TOKEN` when the execution workflow is admitted, or as a secret environment variable in an approved runner.
3. Never paste the token into ChatGPT, an issue, a commit, a log, or repository variables.

The first live acceptance test is read-only:

```bash
RAILWAY_PROJECT_TOKEN='...' python railway_control.py scope
```

Expected result: Railway returns only `projectId` and `environmentId` for the scoped project token. No deployment or variable changes occur.

The second read-only test uses live schema introspection before adding mutation code:

```bash
RAILWAY_PROJECT_TOKEN='...' python railway_control.py schema Mutation
```

## Governance

- Read-only queries may be automated after the token is installed.
- Production mutations (deploy, redeploy, restart, rollback, variable writes, service changes, volume changes, deletes) remain fail-closed until their live schema is verified and an exact approval binds action, target, payload/version and rollback evidence.
- Tokens are environment-only and must never be serialized by NEXUS.
- A successful Railway deployment status is not sufficient production proof. Run `production_probe.py` after any approved production deployment.
- Do not retry a Railway mutation after an HTTP 200 response merely because GraphQL returned an error; inspect the `errors` array and trace ID first.

## Acceptance criteria for v0.1

- unit tests prove correct project-token header selection;
- ambiguous/missing credentials fail closed;
- GraphQL `errors` returned with HTTP 200 fail closed;
- live `scope` succeeds with a project token;
- no mutation entry point exists in v0.1;
- token is absent from git history and logs.

## Next promotion

After the read-only live acceptance test passes, add narrowly typed operations one at a time from Railway's live introspected schema. The first proposed write vertical is `deploy exact Git commit -> wait for Railway status -> run NEXUS production probe -> record evidence -> rollback on failed acceptance`, subject to exact production approval.
