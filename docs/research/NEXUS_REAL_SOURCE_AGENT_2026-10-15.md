# NEXUS v3: real public-source researcher, bounded experimental integration

## Honest scope and recovery

Started from verified `bd2568fc6bea59d2f8913b277cf012c925dfe584`.
Read its report and original 1660-pass log; independently recomputed the stored
log SHA256 and matched its manifest. Independently reran 32 focused tests: all
passed in 4.57s. Historical full-suite result was not initially claimed reproduced.
Current isolated branch: `codex/real-research-agent-2026-10-15`.

This implementation is a **deterministic real-source research worker, not an LLM
reasoning agent**. It performs a real task, unlike the previous placeholder:
retrieve official repository metadata and latest release; validate entity identity,
extract six bounded fields and attach raw source bytes, URL, retrieval time,
SHA256 and an explicit maintenance CLAIM. It cannot answer arbitrary research
questions or qualify buyers. The request for a real LLM agent remains partially
blocked: no usable free local model was verified, no model/API budget authorized.
Do not relabel this as model intelligence or advertise the entire v3 mission done.

## Candidate and connector audit

Existing catalog contains OpenAI Agents SDK, PydanticAI, LangGraph, Temporal and
other experimental/deferred candidates; catalog presence proves neither installation
nor health. Official maintained candidate sources were refreshed through web reads:

- https://github.com/openai/openai-agents-python/releases
- https://openai.github.io/openai-agents-python/release/
- https://github.com/pydantic/pydantic-ai/releases
- https://github.com/pydantic/pydantic-ai/blob/main/docs/version-policy.md

Public GitHub API live evidence for OpenAI SDK reports MIT, not archived, pushed
2026-10-15T02:22:26Z and latest release v0.24.0 published 02:20:12Z. This can
supersede stale search-index release labels; it is still a single-provider CLAIM,
not security approval or a reason to install. Pydantic official release search
showed recent September releases, but exact current version was not API-verified.
Both require a model backend for reasoning. No SDK, model, dependency, credentials
or persistent service was installed; avoid framework count as a success metric.

Selected executor: existing NEXUS router with a fixed standard-library public
GitHub research adapter and an experiment-scoped AgentCatalogEntry. This is a
bounded local extension, not adoption of an external framework. Existing connector
configuration and callable GitHub/Exa/Drive/Notion tools were inspected. Their
permissions/configuration are static observations; health and cost are UNKNOWN
unless probed. No paid search/enrichment/model calls were made. `ollama` and
`llama-server` were not found on PATH; this is not proof no model exists elsewhere.

## Integration and controls

Reuse `project_control_plane`, catalog validation, `AutonomyStore`, lease fencing,
atomic checkpoints, journal, stop/cancel and `Supervisor`. Refactor only fixed
executor hooks/action/roles; default sequential execution. Different action keys
prevent the synthetic runner from claiming research work. Same queue database;
no new database or approval store. A task name cannot be silently reused across
executors because catalog-bound submission digest conflicts fail closed.

Only `PRJ-NEXUS-SANDBOX`; action remains SYNTHETIC_TEST as the inherited deny-only
sandbox permission label, but evidence is REAL public data and clearly labelled
CLAIM. Commercial authority is never asserted. Two fixed URLs only:
`https://api.github.com/repos/openai/openai-agents-python` and `/releases/latest`.
Only unauthenticated GET, TLS, fixed host/path, no proxy/cookies/redirect/auth,
65536 bytes per response, socket timeout 5s, read loop deadline 8s per source,
20s post-acquisition task deadline. System DNS resolution has no separately
preemptive deadline; do not claim a hard end-to-end wall clock guarantee.
Maximum three queued attempts, two source reads per attempt; failed/crashed
attempts may repeat safe GETs. No exactly-once network claim. A failing acquisition
leaves the lease for bounded crash recovery; retries ultimately become dead letters.
Failure is never converted into evidence of absence. Exceptions are redacted.

Freshness, exact source identity, output field types, source-body hashes, evidence
bindings and project/task ownership are validated before checkpoint completion.
Remote health is UNKNOWN before execution, OBSERVED_READ_OK after recent successful
reads, STALE after five minutes. Router planning checks local executor eligibility;
it does not fabricate connector health. Provider content is data, never instructions.
Test transport injection is trusted internal Python only, never an HTTP registration
or source field. Only application-append-only journaling, not tamper-proof storage.

The existing authenticated read-only console now includes the research queue view.
No execution, approval or provider-registration HTTP endpoint was introduced.
Supervisor acceptance proves packet completeness/binding, not independent truth.

## Commands, tests and benchmark

Interpreter: `C:/Users/AvallPc/nexus-business-os/.venv/Scripts/python.exe`, Python
3.14.7/Windows. `PYTHONPATH=src`; no package changes. Commands executed:

```text
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-realagent-baseline tests/test_agent_router_pilot.py tests/test_agent_router_bridge.py tests/test_router_runtime.py tests/test_router_console.py
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-realagent-focused tests/test_public_research_agent.py tests/test_router_runtime.py tests/test_router_console.py tests/test_agent_router_bridge.py tests/test_agent_router_pilot.py
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-realagent-full tests evals
python -m pytest -q -p no:cacheprovider --basetemp <writable>/data/research/pytest-realagent-full-final tests evals
python benchmark_public_research_agent.py --capture data/research/public-agent-live-2026-10-15.json --output data/research/public-agent-frozen-rerun-2026-10-15.json
```

Baseline 32 passed; first focused integration 44 passed. First full run 1672
passed; added five transport-denial/redaction tests, then reran full suite.
Final count and exact hashes: `data/research/public-agent-verification-2026-10-15.json`.
One upstream Starlette/httpx deprecation warning; no framework upgrade performed.
Negative tests: cross-project result, wrong repository/URL, future/stale source,
hash/field/evidence tampering, excessive body size, redirects/403/429/500, redacted
provider failures, stale attempt recovery and completed replay. Existing router
and full regressions retain cancel/stop/budget/isolation/approval/crash checks.

Live invocation used `PublicResearchRuntime(<disposable sandbox queue path>)`,
`submit('public_agent_live_001')`, `drain()` and `review(...)`; the stored output
is `data/research/public-agent-live-2026-10-15.json`. One live task succeeded,
two HTTP GETs, 1.3789565s, two source documents, one independent source family.
Reproducible offline replays: ten runs, six fields exact per run (60/60), complete
bound evidence, zero duplicate execution after restart. Original frozen median
0.0215294s; rerun entry-point median 0.031588s. Timing varies; these do not include
network and cannot predict live latency or recovery reliability.

Synthetic baseline has zero real-source document yield; new path yields two.
Sequential synthetic baseline measured 0.0619404s. Different work/network means
this is NOT a fair latency/accuracy speedup comparison. Six-field exact match
against the saved original JSON measures structured extraction, not held-out
semantic accuracy, independent source verification or commercial usefulness.
General live reliability UNKNOWN (n=1). Verified commercial evidence yield zero.
Model/API monetary cost zero in this workload; total session token use UNKNOWN.
Existing allocator executed: history1000/evidence2500/working7000/output1500.

## Authority, handoff, rollback and approval boundary

Registry/Master HOLD persists; new `bootstrap_chat` evidence is BLOCK. This run
cannot infer canonical authority from repository metadata. Existing project memory
and self-improvement cycle store distilled evidence pointers only. Cycle PARTIAL,
no learning/policy promotion. No unrelated worktree changes were overwritten.

Existing `coordination_kit` generates the local, git-bound handoff after the code
commit and an exact-head focused rerun. Handoff is for review, not an authorization
to message every chat. No external message was sent. Full run binds the tested
source file hashes; exact-head focused result binds the immutable code commit.

Rollback: revert this development commit; retain the shared queue and journal.
Old synthetic action cannot claim research work. Disable the experimental adapter
without deleting evidence or restoring production databases. No external write to
undo. Recovery: initialize `PublicResearchRuntime` with the SAME sandbox queue;
expired attempts can be reclaimed, completed tasks do not fetch again. A crash
before checkpoint may repeat two idempotent reads. Do not install a service.

Next approval boundary: exact commit/branch publication for CI; separately select
an existing local model or approve a specific provider/model, data scope and hard
cost ceiling before introducing LLM reasoning. Resolving Registry/Master remains
required before commercial decisions. No push, merge, deploy, persistent install,
paid charge, credential change or permission expansion occurred.
