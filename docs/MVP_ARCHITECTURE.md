# NEXUS Autopilot v1.1 — MVP Architecture and Phase 1

Date: 2026-08-20

## Decision

Build one modular monolith that proves one safe vertical workflow:

`normalized event -> project resolution -> evidence classification -> safe draft -> approval request -> exact one-time execution`

Do not add Redis, microservices, autonomous browser control, multi-agent orchestration, or write-enabled connectors until this workflow is measured end to end.

## Maturity statement

- **Implemented and unit-tested:** event idempotency, queue leases/retries/dead-lettering, project policy, evidence contracts, exact-scope approvals, audit hash chain, source failover, budget checks, archive recovery and bounded execution scheduling.
- **Implemented but not live-validated in v1.1:** FastAPI container and OpenAI Responses API adapter.
- **Not implemented:** connector OAuth/webhooks, approval user interface, PostgreSQL migration, external action executor, backup/restore rehearsal and production deployment.
- **Known external state:** Apollo remains `AUTH_BROKEN / OPTIONAL`; it is not on the critical path.

## Trust boundaries

1. Connector inputs are untrusted until normalized and linked to provenance.
2. Model output is a proposal, never authority to act.
3. Approval authorizes one exact action digest, not a category of actions.
4. Connector credentials remain outside prompts, source control, logs and handoff archives.
5. Production writes are disabled until an executor verifies approval, digest, expiry, connector scope and idempotency.

## Repository structure

- `api.py` — FastAPI ingestion boundary.
- `contracts.py` — versioned event and evidence contracts.
- `state.py` — idempotent event persistence.
- `autonomy.py` — queue, leases, retry, budget and circuit breaker.
- `approvals.py` — pending/approved/denied/expired/consumed lifecycle.
- `audit.py` — append-only tamper-evident hash chain.
- `agent.py` / `openai_client.py` — model boundary.
- `projects.py` / `policy.py` / `intake.py` — project and action policy.
- `source_failover.py` / `capability_health.py` — connector isolation.
- `evals/` — executable acceptance evidence.
- `Dockerfile` — portable non-root runtime.

## Event contract: `nexus.event.v1`

Required fields: `event_id`, `project_id`, `event_type`, `source`, `occurred_at`, `received_at`, and object `payload`. Times require timezone. `correlation_id` is optional. Canonical SHA-256 detects event-ID/payload collisions.

## Evidence contract

Classes are exactly `FACT`, `CLAIM`, `ESTIMATE`, `ASSUMPTION`, and `UNKNOWN`. A Fact without `source_ref` is rejected. Every record carries project, observation time and confidence. Confidence is metadata, not a statistical probability unless calibrated later.

## Action Gate

- `AUTO_READ`: read, classify, summarize.
- `AUTO_PREPARE`: research, compare, draft, local test.
- `APPROVAL_REQUIRED`: send/reply/forward, publish, commit/push/merge, deploy, payment, contract, permission change and external database write.
- `PROHIBITED`: unknown capability or any security/legal/access bypass.

Approval scope is the digest of `project_id + action + target + parameters`. It has an ID, decider, expiration and consumption timestamp. Target or parameter changes invalidate it; successful consumption makes replay impossible.

## Phase 1 acceptance criteria

1. Duplicate event with identical body is ignored; same ID with changed body is rejected.
2. Naive timestamps and unsupported schemas are rejected.
3. A Fact without a source is rejected.
4. Heat Treatment remains HOLD and Boyu outreach remains forbidden.
5. Apollo failure does not block HubSpot/official-web read lanes.
6. External action without approval is blocked.
7. Approved action can run once only, before expiry, against the exact target and parameters.
8. Audit-chain tampering is detected.
9. All unit tests pass in a clean Python 3.11+ environment.
10. No live email, CRM write, Git operation, deploy or payment occurs during MVP validation.

## Cost model

### OpenAI API — verified rates used

The 2026-08-20 official standard short-context prices for `gpt-5.6-luna` are $0.10/M input tokens and $0.60/M output tokens. `gpt-5.6-terra` is $1/M input and $6/M output. Tool charges such as web search are separate.

| Scenario | Runs/month | Tokens/run (in/out) | Luna model estimate | Terra model estimate |
|---|---:|---:|---:|---:|
| Pilot | 300 | 4,000 / 800 | $0.26 | $2.64 |
| Working | 1,500 | 8,000 / 1,500 | $2.55 | $25.50 |
| Heavy | 6,000 | 12,000 / 2,500 | $16.20 | $162.00 |

These are estimates, exclude connector/tool charges, retries, long-context uplift and regional-processing uplift, and should be enforced with a hard monthly budget.

### Hosting estimate

- Local/offline pilot: $0 hosting.
- Railway Hobby: $5 minimum monthly usage, appropriate for an early private pilot.
- Small production baseline: approximately $25–$60/month for always-on app/database/backups; actual usage and provider choices control the result.
- Supabase Pro starts at $25/month; point-in-time recovery can add material cost and is not part of Phase 1.

### Development estimate

- Executable private MVP with one read connector and approval UI: **80–140 engineering hours**.
- Production hardening with Gmail/Notion/HubSpot/GitHub connectors, PostgreSQL migration, monitoring, restore drill and security review: **250–500 engineering hours total**.

These are planning estimates, not vendor quotations. OAuth approvals, data quality and connector edge cases are the largest uncertainty.

## Phase 1 execution order

1. Freeze contracts and current 47-test regression baseline.
2. Install the downloaded API key only in the chosen runtime secret store; never upload it to chat or Git.
3. Run one Responses API smoke test with a $5 hard project budget.
4. Add Gmail read-only ingestion for one label/thread workflow.
5. Produce a Hydrotester or KCl evidence brief and approval request without sending.
6. Build a minimal approval inbox for approve/deny; no broad approvals.
7. Execute one approved low-risk test action in a sandbox destination.
8. Measure latency, token cost, duplicate rate, false facts and recovery behavior.
9. Only then decide whether PostgreSQL and a separate worker are justified.

## Highest-value next proof

Ingest one real Gmail thread read-only, classify its evidence, generate a draft, and verify that NEXUS cannot send it until an exact single-use approval is consumed.
