# Capability Expansion v7 — Context + High-Risk Quarantine — 2026-10-07
Status: IMPLEMENTED / PENDING CI

## Context
- wiztek-llc/context-ledger: MERGE_NATIVE. Novel mechanism = restorable compression bound to exact Git SHA.
- ZhengShuaiMing/long-task-context: HIGH_OVERLAP; checkpoint discipline useful, separate runtime unnecessary.

## Browser/research
- That1Drifter/browse-mcp: QUARANTINE_SANDBOX_ONLY. Useful accessibility snapshots, page diffs, Readability and lean tool exposure. Recent security fix for path confinement proves host-write review is mandatory.
- cedarsaam/agent-search: SANDBOX_CANDIDATE. Useful meta-search, extraction, citation/RAG and SSRF guard; no need to replace canonical research adapters until benchmark wins.
- LearningCircuit/local-deep-research: BENCHMARK_CANDIDATE for private/local document research and SearXNG/local-model fallback.

## Eval
- future-agi/future-agi: BENCHMARK_DONOR; large active stack, high overlap with native telemetry/evals.
- langchain-ai/agentevals: BENCHMARK_CANDIDATE for trajectory evaluation.

## High-risk policy
Discovery of dangerous candidates is allowed for defensive analysis. Capabilities involving security/access-control bypass or sanctions evasion are rejected. Arbitrary code, host write, credential access, unrestricted network, persistence and browser-write candidates are quarantine-only and never execute directly on the NEXUS host.

## Acceptance
A quarantined candidate can graduate only after: pinned source/version; license; dependency/SBOM review where available; no secrets; isolated filesystem/network/credentials; deterministic fixture; egress/write policy; regression; measurable gain; rollback; exact approval if external/production effects remain.
