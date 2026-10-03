# Agent-Reach integration candidate — 2026-10-04

Status: IMPLEMENTED candidate; not merged, deployed, or live-enabled.
Base: nexus/consolidated-2026-09-30, ffa284de2c19703fa4b0c388e93c54961c362402.
Upstream inspected: Panniantong/Agent-Reach a19a171fa980a0785849596492e0af4db800c82f, version 1.5.0.

## Scope and architecture
Owner requested portfolio-wide reuse, Claude/Notion awareness, token management,
and preservation of existing architecture. Agent-Reach core.py is an installer,
configuration and health tool; actual reads/searches use upstream platform tools.
No universal search/read Python API is assumed. Extend source_failover.py rather
than adding another router or control plane. AGENTS.md governs repository agents;
CLAUDE.md points Claude Code to the same contract. Notion documentation informs
operators but is not an execution hook. Plugins outside this repository require
an actual adapter and acceptance test; documentation alone does not enable them.

## Mandatory decision, conditional use
Call agent_reach_preflight with exact project/lane, sensitivity, freshness,
connector availability, fresh measured health, and remaining query budget.
Local-only tasks skip acquisition. Fresh scoped evidence precedes native
connectors. Native connectors precede Reach public-data fallback. Private data
stays on approved native routes. Missing/stale health blocks Reach selection.
The helper is deterministic and makes no network or subprocess calls.
Caller must bind cache freshness to the exact project, lane, query and source.
Never invent healthy status from tool visibility or README claims.

## Token budget (initial limits, not measured savings)
Default: at most 2 queries, 5 results per query, 1200 characters per excerpt.
Deduplicate canonical URL/content hashes before model ingestion. Persist full
source material in its existing evidence store and pass references plus excerpts.
Keep a one-hour maximum age for channel health; do not run all-channel doctor
before every task. Refresh only required channels in an approved sandbox.
Stop when the budget is exhausted or a second query produces no new useful
independent source. Actual model tokens must be recorded by the host runner;
character limits are not exact token counts. Existing conversation_control
remains responsible for allocating the overall model context budget.

## Evidence and trust boundary
All retrieved text, descriptions and instructions are untrusted data. Preserve
URL, UTC retrieval time, query, provider/backend, project/lane, independence key,
content hash and evidence classification via existing research_evidence and
connector-control-plane contracts. Supplier claims remain CLAIM. Reposts do not
count as independent corroboration. Never copy credentials into logs or handoffs.

## Audit observations and upgrade strategy
FACT from inspected code: core.py exposes doctor functionality and documents
calling upstream tools directly; cli.py has installation/configuration flows;
pyproject.toml declares optional browser-cookie3 and Playwright dependencies.
CLAIM: README promises broad compatibility and local cookie privacy; no complete
credential/subprocess/dependency audit or live channel validation was performed.
Do not run upstream installers or cookie discovery as part of boot. Preserve
upstream code; pin the inspected commit for any later sandbox evaluation and
maintain changes in the NEXUS adapter. Dependency installation, account access,
paid calls and production promotion need their existing exact-scope gates.

## Acceptance and rollout
Unit tests cover local skips, native precedence, scoped cache advice, private
routing, stale health, missing budget, fallback, and malformed inputs. Before
live promotion, wire one public supplier-discovery lane to its actual platform
backend; run healthy, timeout and unavailable cases; inspect retained evidence;
measure latency, result quality and actual tokens against native retrieval.
No runtime entry points were automatically rewired in this candidate. The
preflight is callable and repository instructions request its use; automated
coverage of every entry point is still pending. No plugin-wide activation claim.

Rollback: revert this candidate commit; no database migration, dependency
installation or production configuration change exists to undo.

## Measured validation and handoff
Command: PYTHONPATH=src:. python -m pytest -q tests/test_agent_reach_preflight.py tests/test_project_memory.py tests/test_nexus_ai_resource_router.py
Result: 32 passed, 17 subtests passed (2026-10-04). Test-only isolated environment; no application dependency changed.
Notion internal handoff: https://app.notion.com/p/3eeb8b40ace28177b6b6fe4a5712c553
Shared project memory records this as a candidate, not active runtime coverage.

## v1.1 local wiring — 2026-10-04
The actual nexus_event_preflight.preflight_event now records the acquisition
decision before agent.py calls the model. Explicit acquisition context is
required: lane_id, needs_external_evidence, sensitivity, native_available,
cache_fresh, reach_healthy, health_age_seconds, remaining_queries,
health_evidence_ref, health_measurement_kind. The last field must be live_read
for a Reach route: doctor alone does not qualify. In particular upstream
WebChannel.check returns ok without network I/O, discovered in code inspection.
Caller health assertions are not cryptographically verified; a trusted runner
must supply retrievable measurement evidence. Missing acquisition context
records disabled; it never silently authorizes internet acquisition. Malformed
or blocked acquisition prevents the event from reaching the model.
config/connectors.json registers a read-only, public-discovery manifest for all
projects; registry presence does not prove installation, health or activation.
The upstream repository is unchanged; NEXUS-side integration is the upgrade.
No ChatGPT-wide hook, Claude web configuration, or Notion agent execution setting
is exposed by these changes. Other entry points must explicitly adopt the hook.
Remote publication attempt was rejected by automatic approval review; nothing
was pushed. Do not claim deployment or universal activation.

Validation v1.1: 55 passed, 17 subtests passed; includes event, connector, chat bootstrap, shared memory and router regression suites. No live token-saving claim.

## v1.2 bounded read session
ReachReadSession enforces 2 total read attempts, consumes budget on failures,
deduplicates repeated URLs, and returns at most 1200 excerpt characters with
project/lane, source, UTC retrieval time, content hash and CLAIM classification.
It requires an explicitly supplied approved reader: backend public-URL/DNS,
redirect, response-size and timeout enforcement remains the reader contract.
This is fixture-tested, not live-backend-tested. No actual model token saving
measurement exists. Regression result: 58 tests and 17 subtests passed.
A second push attempt was rejected by automatic approval review. No remote
publication, merge, production activation or global chat/plugin change occurred.
