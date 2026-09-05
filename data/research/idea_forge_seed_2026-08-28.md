# NEXUS Idea Forge Seed — 2026-08-28

Status: DISCOVERY / VALIDATION INPUT. No item below is authority or permission to deploy, contact, spend, connect credentials or modify production.

## Source-aligned operating rule
Use the NEXUS discovery funnel: Discovery → Evidence → Deduplication → Validation → Scoring → Portfolio comparison → Recommend/Watch/Reject → Human authorization → Execution. Prefer verified outcome and gross-margin learning over idea volume.

## High-priority experiment candidates

### IDEA-AI-01 — Coding Sandbox Tournament
Problem: coding-worker choice is still mostly capability-driven rather than NEXUS-outcome-driven.
Candidates: OpenAI Sandbox Agents, OpenCode, OpenHands, Goose, Open SWE, Microsoft Agent Framework CodeAct/Harness.
Experiment: frozen repository task, identical snapshot, identical acceptance contract, zero credentials, no network unless explicitly isolated; compare human corrections, elapsed time, regressions, policy/security findings and cost over >=3 clean runs.
Success: one adapter beats baseline on at least one meaningful dimension without regression or authority expansion.

### IDEA-AI-02 — Hindsight temporal memory benchmark
Research signal: ACL 2026 Hindsight separates world/experience/observation/opinion memory and provides temporal retrieval; this maps well to NEXUS FACT/CLAIM/UNKNOWN and evolving-state requirements.
Experiment: synthetic contradictory history across KCl/Hydrotester/Can Forming; require current-fact recall, historical point-in-time recall, provenance preservation and zero cross-project leakage.
Do not replace Source Registry or canonical masters.

### IDEA-AI-03 — Stateless MCP Gateway profile
Research signal: MCP 2026-07-28 introduces a stateless core, header routing, cacheable list results, stronger authorization and formal extensions/tasks.
Experiment: update NEXUS MCP Broker compatibility profile for the new spec; test read-only registry ingestion and header-based policy routing. No external MCP receives credentials in the experiment.

### IDEA-AI-04 — Cloudflare durable/browser worker benchmark
Research signal: Cloudflare Agents SDK 2026 adds Browser Run, Code Mode, background sub-agents and recovery through deploy/eviction/reconnect cycles.
Experiment: compare one browser-research workflow and one long-running synthetic workflow against current NEXUS path. Measure recovery, duplicate prevention, cost and policy transparency.

### IDEA-AI-05 — Agent Harness / typed-control benchmark
Research signal: Microsoft Agent Framework 1.0 GA and 2026 Agent Harness/CodeAct patterns provide production-focused control, middleware and multi-step workflows.
Experiment: one frozen bounded workflow only. Reject if it duplicates NEXUS control-plane logic without lower complexity or better recovery.

## Commercial / business growth ideas

### IDEA-COM-01 — Procurement Intelligence Product
Turn the proven NEXUS supplier/evidence/quote/approval workflow into a reusable internal product first, then potentially a sellable B2B procurement intelligence service for industrial importers/manufacturers.
Fast evidence test: run on one additional real procurement category and measure time-to-qualified-supplier, duplicate avoidance, evidence completeness and quote-comparison speed versus manual baseline.

### IDEA-COM-02 — Industrial Installed-Base Opportunity Radar
Build living profiles of factories/lines/equipment and infer likely replacement, retrofit, spare-parts and capacity-expansion needs from public CAPEX, maintenance, hiring, tender and production signals.
Fast evidence test: 20 companies in one adjacent industrial niche; produce 5 evidence-backed need hypotheses; require at least 2 independently verifiable high-quality signals per hypothesis.

### IDEA-COM-03 — Supplier Failure / Route Resilience Radar
For each active procurement project, continuously maintain at least two independent supply routes and detect concentration, sanctions/payment/logistics risk and supplier silence.
Fast evidence test: Hydrotester or KCl; quantify route count, response quality and time-to-backup compared with current pipeline.

### IDEA-COM-04 — Quote Intelligence & Negotiation Memory
Normalize commercial terms across vendors and learn which price/payment/warranty/commissioning/spares concessions are historically attainable, while keeping project boundaries.
Fast evidence test: historical sanitized quote set; identify missing terms and negotiation deltas without inventing benchmarks.

### IDEA-COM-05 — Warm-Path Relationship Engine
Map people→companies→referrals→OEMs→buyers, with role confidence and evidence dates. Prioritize genuine warm paths before cold outreach.
Fast evidence test: one project; compare valid-response rate and referral yield from warm-path leads versus cold leads. No automatic outreach.

## Engineering ideas

### IDEA-ENG-01 — FAT/Test-Plan Generator
Given canonical requirements + supplier claims, generate a requirement-linked FAT matrix with measurement method, acceptance range, evidence artifact and witness status.
Fast evidence test: Hydrotester 120 MPa duty envelope and throughput/hold-time requirements.

### IDEA-ENG-02 — Supplier Proposal Evidence Compiler
Extend Proposal Delta Engine to ingest proposal tables and emit: requirement, supplier statement, epistemic class, source locator, deviation, missing evidence and requested proof.
Fast evidence test: one GH/Marley hydrotester proposal and one Can Forming proposal, without transferring values between projects.

### IDEA-ENG-03 — Engineering Contradiction Replay
Whenever a requirement changes, replay all prior proposal decisions and flag which qualifications become stale.
Fast evidence test: synthetic change of one Hydrotester requirement and prove affected decisions are invalidated while unrelated project records stay untouched.

## Executive / automation ideas

### IDEA-OPS-01 — Outcome Ledger as the optimization target
Every automated workflow should emit measurable outcome fields: time saved, human corrections, business value, conversion stage, risk prevented and whether next action occurred.
Fast evidence test: three current workflows; reject any automation that cannot produce an auditable outcome record.

### IDEA-OPS-02 — Daily Autonomous Work Queue
Executive Check should not only report state; it should build a ranked queue of safe reversible tasks, execute bounded read/research/draft/test steps, and checkpoint evidence/result.
Fast evidence test: one day of tasks across two projects with zero duplicate outreach and no protected action.

### IDEA-OPS-03 — Failure Injection Lab
Create deterministic fault scenarios: stale registry, connector timeout, duplicated email, malicious prompt injection, partial write, wrong project ID, approval mutation and restart mid-workflow.
Fast evidence test: all critical paths fail closed or recover without duplicate consequential action.

## Product / UI ideas

### IDEA-PROD-01 — NEXUS Mission Control
A single operator UI showing current canonical state, live evidence freshness, tasks, blockers, exact approvals, experiment results, opportunity radar, technology radar and outcome metrics.
Build only after the backend contracts are stable; avoid another dashboard that becomes a parallel source of truth.

### IDEA-PROD-02 — Decision Replay
For any major decision, show exactly what evidence, contradictions, model/tool outputs, approvals and rules produced it, and replay under a newer source version.
This could become a differentiating trust feature for NEXUS.

## Keep / revisit list from current research
- OpenAI Agents SDK / Sandbox Agents: EXPERIMENT
- OpenCode: EXPERIMENT
- OpenHands: EXPERIMENT
- Goose: EXPERIMENT
- Open SWE: EXPERIMENT
- Hindsight: RESEARCH → MEMORY BENCHMARK
- Graphiti: WATCH → TEMPORAL GRAPH BENCHMARK when repeated temporal retrieval failures are measured
- Mem0 / Letta / Cognee: WATCH / comparative memory cohort
- Microsoft Agent Framework: RESEARCH / bounded benchmark
- Cloudflare Agents SDK: RESEARCH / browser + durable worker benchmark
- MCP 2026-07-28 spec: HIGH-PRIORITY COMPATIBILITY RESEARCH
- Temporal: DEFER until multi-day recovery pain is measured
- LangGraph: DEFER unless agent-state graph provides measurable benefit over current state model
- OmniRoute: SANDBOX_EXPERIMENT only

## Selection principle
Keep the catalog broad; keep production narrow. A candidate can remain useful for years in DISCOVERED/WATCH/DEFERRED state. Build/connect only when a repeated measurable problem, acceptance test, rollback and evidence justify it.
