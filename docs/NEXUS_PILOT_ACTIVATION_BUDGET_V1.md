# NEXUS Pilot Activation and Budget Strategy v1

Status: DRAFT / NO LIVE INSTALL / NO ALWAYS-ON DEPLOYMENT.

## Decision

Keep NEXUS as the authority. Trial only one open-source component at a time, read-only, with synthetic data. Prefer existing GitHub Actions CI and deterministic Python tests over a new scheduler, database, orchestrator or paid API.

## Candidate sequence

1. Existing NEXUS simulation and shared-state board: exact-head CI + readback proof.
2. Marketplace adapter compatibility: compare existing schema against freelancezero (no live clone/install until security and license review).
3. CRM compatibility: evaluate Twenty read-only in sandbox, without external writes.
4. Agent runner: compare existing Supervisor against LangGraph/CrewAI only after a measured failure of the current runner.
5. Persistent scheduler: activate only after target host, credentials strategy, rollback, monitoring, explicit operating budget and approval are documented.

## Budget tiers

- Tier 0: $0 incremental spend, synthetic fixtures, repo-based CI, no paid calls.
- Tier 1: user-approved bounded pilot with explicit maximum per experiment and monthly cap.
- Tier 2: production-like deployment only after security review, incident response, backups, observed pilot value and exact approval.

Do not interpret these tiers as available account balance. Measured provider usage is UNKNOWN until read from billing evidence.

## Always-on prerequisites

Document host/provider, service identity, secret storage, start/stop mechanism, logs, retention, alerting, backup/restore test, egress allowlist, API rate limits, quota enforcement, and kill switch. Require explicit authorization for target and configuration. Never claim a GitHub commit automatically changes all ChatGPT chats.

## Steel backlog

Maintain steel commercial discovery and project masters separately. No automatic customer outreach. Prioritize current demand evidence, buyer identity, relationship binding and product/stock eligibility before lead volume.
