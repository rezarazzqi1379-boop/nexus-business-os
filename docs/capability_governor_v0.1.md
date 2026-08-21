# NEXUS Capability Governor v0.1

Status: DESIGNED / CHECKPOINTED — not yet production automation
Date: 2026-08-22

## Purpose
Prevent tool/model sprawl. A candidate AI capability is admitted only when it creates measurable marginal value over the current NEXUS stack.

## Admission pipeline
Need -> Candidate -> Evidence -> Small reversible test -> Compare -> Risk/Cost review -> ADOPT | WATCH | REJECT

## Hard gates
1. No candidate is promoted from marketing claims alone.
2. Primary/official documentation is preferred for capability claims; independent evidence is required when practical for reliability/performance claims.
3. A score is heuristic until calibrated on NEXUS outcomes.
4. New connectors default to read-only/minimum scope.
5. External commercial actions, payments, contracts, production changes, confidential disclosure and final qualification remain human-gated.
6. A failed tool call must not imply task completion.
7. Duplicate capability is rejected unless it improves a measured dimension.

## Scorecard (100)
- Unique capability / marginal benefit: 20
- Reliability and recoverability: 15
- Evidence quality: 15
- Integration fit (MCP/API/SDK/current stack): 10
- Observability/evaluation: 10
- Security/least privilege: 10
- Cost efficiency: 10
- Reversibility/lock-in: 5
- Learning value for NEXUS engineering: 5

Decision bands:
- 85-100: smallest reversible test required; adoption only after pass
- 70-84: WATCH / targeted experiment
- <70: REJECT or defer

## Current architecture decisions
### OpenAI Agents SDK — TEST / likely ADOPT as optional orchestration runtime
Why: built-in tools, handoffs, guardrails, sessions, human-in-the-loop, MCP integration and tracing. Do not rewrite proven NEXUS domain modules around it before a benchmark.

### MCP — ADOPT as agent-to-tool interoperability layer
Use tool filtering, namespacing/collision controls, approval policy and traceability. Treat MCP content/tool output as untrusted input.

### A2A — WATCH / future agent-to-agent boundary
Useful when NEXUS actually operates independent heterogeneous agent services. Do not add merely because the protocol exists.

### Cloudflare Agents/Durable infrastructure — WATCH / sandbox benchmark
Potentially useful for durable remote agents and deployment. Must beat simpler hosting/runtime options on a real NEXUS workload before adoption.

### Exa — ADOPTED FOR DISCOVERY, NOT AUTHORITY
Search/discovery engine; outputs require source-authority classification and verification.

### Consensus — ADOPT FOR ACADEMIC CRITIC USE CASES
Use when peer-reviewed evidence materially improves decisions. It is not a general business/web authority engine.

## Model Critic Harness v0.1 contract
Input: task, primary answer, claims, evidence set, risk class.

Independent critic output must be structured as:
- disputed_claims[]
- missing_evidence[]
- alternative_hypotheses[]
- failure_modes[]
- proposed_tests[]
- confidence_notes[]

Rules:
- Critic output is CLAIM, not FACT.
- Disagreement triggers evidence verification, not majority voting.
- Do not expose confidential project data to an external model unless necessary and approved.
- For low-risk routine work, do not invoke a second model without expected marginal value.

## Benchmark metrics
- Unsupported claim rate
- Stale-authority error rate
- Cross-project contamination rate
- False-completion rate
- Tool-call failure/recovery rate
- Duplicate action/outreach rate
- Human correction rate
- Task success under constraints
- Time-to-decision
- Tool calls / latency / estimated cost per successful task

## First reversible benchmark
Run the same bounded NEXUS task under:
A) current deterministic/domain-module workflow
B) Agents SDK orchestration wrapper

Keep the same authoritative inputs and acceptance tests. Compare correctness, tool failures, traceability, latency, cost, recovery and human corrections. No production write authority in the benchmark.

## Promotion rule
A new runtime/model/tool is promoted only if it improves at least one important metric without unacceptable regression in safety, correctness, cost, or recoverability.
