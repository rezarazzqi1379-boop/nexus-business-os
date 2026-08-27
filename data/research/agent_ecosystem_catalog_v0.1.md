# NEXUS Agent Ecosystem Catalog v0.1

Status: INTERNAL RESEARCH CATALOG. Not authority. Not an install list. Not permission to connect or execute external tools.

Purpose: keep a durable, searchable memory of agents, frameworks, protocols, MCP infrastructure, coding agents, browser/computer-use agents, memory/eval/automation systems and related infrastructure so useful candidates are not forgotten merely because they are not appropriate today.

## Lifecycle model

`DISCOVERED → WATCH / RESEARCHED → SANDBOX_READY → EXPERIMENT → PILOT → ADOPTED_ADAPTER`

Alternative states remain preserved rather than deleted: `DEFERRED`, `SUPERSEDED`, `REJECTED`, `ARCHIVED`.

Every candidate must retain: source locator, observed date, problem tags, capabilities, lifecycle, revisit triggers, acceptance test, rollback and notes. A deferred candidate is intentionally retained so a future project condition can reactivate evaluation without repeating discovery from zero.

## Initial catalog coverage

The executable seed in `src/nexus_core/agent_catalog.py` includes OpenAI Agents SDK, OpenAI Sandbox Agents, OpenCode, OpenHands, Google ADK, Microsoft Agent Framework, LangGraph, Temporal, Official MCP Registry, A2A, n8n, Open SWE, Goose, Plandex, Bytebot and UI-TARS Desktop.

This is not claimed to be the complete internet-wide universe. It is the first governed seed of an expanding inventory. Broad discovery feeds should be used for recall; upstream/primary sources are required before promotion.

## Discovery feeds retained for future mining

- Official MCP Registry — authoritative registry service for MCP server discovery metadata, not authority over NEXUS execution policy.
- `Supersynergy/awesome-ai-agents-2026` — broad dated index spanning frameworks, coding agents, protocols, memory, evals, security and deployment.
- `caramaschiHG/awesome-ai-agents-2026` — high-recall directory across 20+ categories.
- `Anandesh-Sharma/awesome-agent-harnesses` — useful map of agent harness architecture, frameworks, coding agents, papers and benchmarks.
- `ShrikeBot/awesome-agent` — autonomous-agent ecosystem map including identity, trust, communication, memory, hosting and marketplaces.
- `GagnDeep/awesome-best-open-source-ai-agents-2026` — open-source framework/coding/browser/self-hosted discovery feed.

These feeds are discovery inputs only. Their claims, star counts, rankings and completeness are not promoted as facts without verification.

## Revisit policy

NEXUS should query the catalog before building a new subsystem. If a matching candidate exists, first ask whether the repeated problem, acceptance test or maturity trigger has changed. New research should append/update lifecycle evidence rather than erasing earlier candidates. Adoption requires the separate Technology Radar / Adoption Gate and regression evidence.

## Current decision principle

Keep the catalog broad; keep the runtime narrow. Discovery can be expansive and persistent, while production adoption remains minimal, measured and reversible.
