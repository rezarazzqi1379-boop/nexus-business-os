# NEXUS Autopilot v2 Cloud Hardened

The canonical deployment target is a managed Linux container with persistent
storage. A Windows installation is **not required**. Local Windows/macOS/Linux
operation remains a recovery and development option.

## Cloud quick start

1. Deploy this directory from a private Git repository to Railway.
2. Attach a persistent volume at `/data`.
3. Set `NEXUS_ACCESS_TOKEN` to a randomly generated value of at least 32
   characters; keep `NEXUS_AUTH_REQUIRED=1`.
4. Use `/ready` as the platform health check and open `/console` with HTTP Basic
   authentication (any username, the token as password).
5. Add `OPENAI_API_KEY` only when live model calls are required. The core,
   canonical-source workflows, UI, tests, approvals, queue, audit and backups
   operate without it.

See `docs/CLOUD_DEPLOYMENT_RUNBOOK.md` and `docs/ADR-001-CANONICAL-CLOUD.md`.

An approval-gated, event-driven OpenAI Responses API MVP for continuing NEXUS work when
the owner is unavailable.

## What it proves

- accepts normalized Gmail/message/project events through `POST /events`;
- persists events in SQLite, ignores completed duplicates, safely retries
  transient failures, and rejects event-ID/payload collisions;
- uses one focused OpenAI agent to classify evidence and recommend next action;
- allows analysis, research, comparison, testing and drafting;
- requires human approval for sends, publishing, merges, deployments, payments,
  contracts, permission changes and external database writes;
- exposes `GET /health` for deployment readiness.
- routes events through a project registry covering Hydrotester, KCl, Can
  Forming, Heat Treatment, food additives, coffee, tinplate PI and portfolio;
- creates hashed `nexus.delegate.v1` packets that another authorized agent or
  ChatGPT bridge can consume without impersonating the owner.
- provides durable leases, exponential retry, dead-letter handling, monthly
  budget enforcement and per-capability circuit breakers without extra services.
- includes a provider-neutral Customer Discovery Network: read-only source
  adapters, evidence-required lead qualification, deterministic ranking,
  deduplication, and snapshot-bound approve-research/reject/hold decisions.
  Lead approval never authorizes outreach.
- adds a fail-closed Capability Health audit that separates manifest state,
  permission-service state and a live read probe; detects contradictory install
  state and flags permissions broader than the measured workflow need.
- adds cost-aware source failover: a broken or unauthorized lead provider is
  skipped without blocking healthy read-only HubSpot and official-web sources.
  Paid sources require an explicit per-query budget.
- adds provider-neutral CRM hygiene checks before lead qualification: missing
  identities, invalid or duplicate domains, website/domain disagreement,
  probable one-character domain typos, and mismatches against separately
  verified fields. The audit is read-only and never invents a correction.
- adds a local ChatGPT export recovery lane for official `conversations.json`
  files: deterministic message recovery, collision detection, evidence-linked
  goal candidates, manual review status, an unbounded active portfolio and a
  separate configurable execution limit. Chat history is never treated as current truth and is never uploaded by
  this module.
- adds a cross-project execution scheduler. Every project can remain active and
  recoverable while only evidence-ready, independent work occupies execution
  slots; waiting and blocked projects retain state without consuming a slot.

Version 1.1 added a versioned event contract, evidence records, an exact-scope
single-use approval store, a tamper-evident audit chain, a FastAPI adapter and a
non-root Docker image. See `docs/MVP_ARCHITECTURE.md` for boundaries, costs and
acceptance criteria.

Version 1.2 adds the tested `nexus.operator.v2` prompt contract and a
deterministic decision triage engine. It preserves contradictions, requires
alternative hypotheses and future signals for material predictions, and ranks
options by commercial value, evidence, reversibility, cost and downside risk.

Version 1.3 adds a provider-neutral Need Radar that turns tender, expansion,
plant-change, hiring, regulatory, email and referral signals into isolated
company/project need hypotheses. It requires retrievable evidence, blocks
claim-only promotion, routes contradictions to manual review, prevents silent
duplicate-company need records and emits research-only briefs that never
authorize outreach.

Version 1.4 adds a Gmail-to-NeedSignal adapter with an explicit untrusted-body
boundary. It binds reviewed observations to retrievable Gmail message evidence,
keeps supplier/integrator replies out of buyer-lead priority queues and proves
that instructions embedded in email bodies cannot grant approvals, select
actions or authorize outreach.

Version 1.4.1 closes a reproduced double-decision race in the approval gate.
Approval decisions now serialize before reading pending state and use an atomic
`status='pending'` compare-and-set update. Exactly one concurrent reviewer can
win; every later or competing decision fails with `approval_not_pending`.

Version 1.5 hardens the full email-classification boundary. The model receives
an explicit untrusted-data envelope and a strict Structured Outputs schema that
contains no action, approval, permission, project, role, fit, timing or
relationship fields. A deterministic local enforcer sources those controls
only from trusted context, requires exact quotes grounded in the original
email, classifies external email assertions as CLAIM and keeps all resulting
briefs research-only. Live model behavior remains unverified until API billing
is active.

Version 1.6 adds a deterministic Entity/Project Resolver in front of that
classifier boundary. Canonical company identity comes only from verified sender
emails or domains, and project-specific role, fit, timing and relationship come
only from registry bindings. Unknown identities, domain typos, unbound project
hints and multi-project ambiguity fail closed. Email subject/body content cannot
select or alter company, project or role.

Version 1.7 adds a dependency-free, responsive Operator Console served by the
existing FastAPI application at `/console`. It implements and tests all 20
agent-interface patterns reviewed from Beautiful UI, plus six NEXUS-specific
controls: evidence ledger, exact action fingerprint, connector health,
constraint guard, cost meter and recovery checkpoint. The pilot is explicitly
read-only: approval buttons are previews and cannot invoke any connector write.

Version 1.8 adds a provider-neutral Markdown Business OS vault compatible with
Obsidian. It includes canonical project indexing, safe asynchronous request
queues, atomic generated outputs, append-only operational audit records, six
workflow templates and a locally generated daily project pulse. The vault does
not require Obsidian, Claude Code or n8n; these may be optional interfaces or
schedulers later. Its API exposure is read-only at `/v1/vault/status`.

Version 1.9 adds a provider-neutral local-runner boundary and an audited MCP
activation registry. OpenWorker is recorded as experimental and disabled by
default: it may receive only secret-free, workspace-scoped, read-only work
packets and can never inherit or consume a NEXUS approval. Six MCP candidates
are catalogued for later one-at-a-time, read-only pilots; none is auto-enabled.

It does not yet contain Gmail OAuth/MCP credentials or a ChatGPT-to-ChatGPT
conversation bridge. Those are separate connector and identity-control layers;
the portable delegation packet is the tested boundary for that future bridge.

## Run

```bash
set -a; . ../.env.local; set +a
python main.py --input data/sample_event.json
```

FastAPI server:

```bash
set -a; . ../.env.local; set +a
PORT=8421 uv run uvicorn api:app --host 127.0.0.1 --port 8421
curl http://127.0.0.1:8421/health
# open http://127.0.0.1:8421/console
```

Tests:

```bash
python -m unittest discover -s evals -v
```

Chat archive recovery (local only; raw statements are omitted by default):

```bash
python chat_archive.py /path/to/conversations.json --output nexus_chat_recovery_report.json
```

The runtime client uses Python's standard library and has no mandatory package
dependency. Agents SDK remains an optional future orchestration layer.

## Production readiness

- Local validation: run the complete suite below; the exact count is reported by the current evidence pack.
- Live API validation: the request reached the OpenAI API, but the project
  returned `insufficient_quota`. Add API billing/credits before the live smoke
  test can complete.
- Do not deploy connectors until the live smoke test passes. Gmail and GitHub
  should begin read-only and every external write must remain approval-gated.

## Next production layers

1. Gmail/GitHub webhook adapters with scoped OAuth and read-only defaults.
2. Durable task queue plus retry/dead-letter policy.
3. Single-use signed approvals tied to exact action digests.
4. Cost budgets, per-project rate limits, observability and kill switch.
5. A user-facing approval inbox instead of autonomous external execution.

## Design sources

The durable queue borrows general reliability patterns, not source code, from
Temporal's Durable Execution and idempotent Activity guidance. Human fallback
and resumable approvals follow the public architectural patterns documented by
n8n. HubSpot's prospecting-agent pattern validates monitored buying signals,
explicit plays and a review inbox, but NEXUS keeps research approval separate
from outreach authorization and avoids credit-consuming automation until a
measured pipeline need exists. NEXUS keeps a single focused agent until evidence
shows that a multi-agent team materially improves outcomes.

Version 1.10 adds a Ruflo (claude-flow) orchestration layer for Claude Code
sessions working in this repository. Twenty-six plugins are declared in
`.claude/settings.json` (`enabledPlugins`): core, swarm, autopilot, workflows,
hybrid vector+graph memory (agentdb, rag-memory, knowledge-graph, rvf),
architecture record-keeping (adr, ddd), security (aidefence, security-audit),
cost-tracker, observability, migrations, testgen, docs, sparc, metaharness,
jujutsu, goals, daa, graph-intelligence, plugin-creator, intelligence, and
cross-installation agent federation (federation). The `ruflo` marketplace
(`ruvnet/ruflo`) is declared at project scope, so `claude plugin install`
resolves it without extra configuration on any machine that clones this repo.
`ruflo doctor --fix` reports 18 passed checks and 10 non-blocking warnings, no
failures; the vector memory database (`.swarm/memory.db`) was rebuilt under
the native storage driver and verified (6/6 checks).

The MCP server declared in `.mcp.json` is not yet live in any session:
activation requires running `claude` interactively in this directory at least
once so it can register the server and load the plugin set. The background
daemon (`ruflo daemon start`) is deliberately not started — it spawns headless
Claude sessions on a schedule and consumes tokens continuously, so starting it
is left as an explicit operator decision, not a default.

`ruflo-federation` publishes swarm-coordination events to a third-party relay
(`relay.ruv.io`) outside this project's own infrastructure. As of this version,
no NEXUS business data (leads, evidence, approvals, canonical sources) is
routed through that layer — only Claude Code coordination events, and only if
and when multi-agent swarm workflows or the daemon are actually activated.
`ruflo-aidefence` is enabled for PII/prompt-injection scanning but its
underlying package (`@claude-flow/aidefence`) is not yet installed locally
(`ruflo doctor` flags this as optional); its MCP tools will fail silently
until `npm install --save @claude-flow/aidefence` is run in a directory ruflo
resolves it from.

Two more plugins were added after the initial Version 1.10 pass:
`ruflo-loop-workers` (recurring-task substrate; declares the scheduling
workers but starts nothing on its own) and `ruflo-business-pods` (ADR-164
Phase 2, v0.1.0-alpha — a sales-pod template and dry-run-only pod runner;
`--live` execution is explicitly reserved for a future phase and is not wired
up here). The plugin count is now 28.
