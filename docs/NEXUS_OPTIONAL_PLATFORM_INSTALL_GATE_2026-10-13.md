# NEXUS optional platform pilot — installation and continuous operation gate v1

Date: 2026-10-13. Lane: PRJ-STEEL-SALES. Draft PR #111. User approved proceeding with installation and continuous integration, but no target host, secret scope, cost ceiling or production endpoint has been verified. **No live installation or daemon activation is claimed.**

## Baseline
- GitHub CI run 38388188315 SUCCESS on prior HEAD eebd4a85f34410644b9aac1ce018b5d658fd4ca6.
- Upstream repository metadata checked: assafelovic/gpt-researcher active, Apache-2.0; langfuse/langfuse and activepieces/activepieces active, GitHub license metadata NOASSERTION (must review full terms).
- NEXUS repo already contains research, evaluation, connector-control and orchestration modules; do not duplicate without a benchmark.

## Installation admission (no production changes)
1. Recover Source Registry and canonical steel-sales master; check main, branch and PR SHA.
2. Select isolated execution host and obtain explicit host-level access. Do not assume GitHub connector grants shell access to Windows or any cloud machine.
3. Inspect candidate license, latest tagged release, dependency manifests, vulnerabilities and outbound telemetry. Pin immutable commit SHA and verify checksum/SBOM.
4. Run synthetic-data, no-secrets pilot in a disposable environment. Block all outbound emails, CRM writes, tender submissions and paid model/API calls. Deny arbitrary command execution and remote tools by default.
5. Compare same 10 steel tender cases against existing NEXUS research pipeline. Measure original-source precision, false-positive active buyer rate, deduplication, execution time, token/API cost, error handling, and no-contact negative tests.
6. Require measurable improvement, bounded resource use, logs with sensitive data redacted, kill switch, idempotency, restart policy and rollback. Keep the new adapter disabled until acceptance.
7. Only after passing all checks, propose explicit activation approval listing target host, pinned version, access scope, data classes, schedule, monthly cost ceiling and rollback. A continuous process cannot be guaranteed from a chat session alone.

## Candidate decisions
- GPT Researcher: FIRST isolated pilot; no permanent install until acceptance.
- Langfuse: DEFER until existing tracing/evals gap is quantified; license and telemetry review mandatory.
- Activepieces: DEFER until a single read-only automation proves benefit over existing scheduler.
- Railway / Render: not installed or connected; no hosting provisioned.

## Independent prompt for Work / local executor

> Recover NEXUS branch and this admission document. Inspect existing research/evals/connector code before installing anything. On an isolated, disposable, nonproduction host, audit and pin GPT Researcher upstream commit and dependencies; prepare an installation plan and offline synthetic smoke test. Never use live company data, API keys, production network, email, CRM or paid calls. Run baseline-vs-candidate evaluation, collect logs and rollback instructions, and commit evidence only to the existing Draft PR. Stop and report BLOCKED if host access, release verification, isolation or dependency security checks are unavailable. Do not merge, deploy, start a permanent service or spend without exact target-specific approval.

## Acceptance
No production or continuous-activation claim unless the specific running host and process, health check, logs, restart behavior, idempotency, isolation, monitoring and rollback are actually observed and tested. Record each separately as DESIGNED, IMPLEMENTED, TESTED, DEPLOYED or PRODUCTION.
