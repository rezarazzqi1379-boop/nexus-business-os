# NEXUS Future Infrastructure Watchlist — 2026-08-28

Status: RESEARCH / EXPERIMENT QUEUE. None of these tools are NEXUS authority. No production adoption is implied.

## Problem-first shortlist

### 1. Temporal memory / evolving facts
Candidates: Graphiti, Hindsight, Mem0, Letta, Cognee.
NEXUS problem: project facts, counterpart state and decisions change over time; retrieval must distinguish current truth, historical truth and superseded evidence.
Acceptance direction: frozen temporal-recall corpus with contradictory/superseded facts; score current-fact accuracy, historical point-in-time accuracy, provenance retention, cross-project leakage, latency and correction burden.
Current position: evaluate only after the in-process governed graph baseline is measured. Do not replace Source Registry or Tier A authority.

### 2. Durable execution / resumable workflows
Candidates: Temporal; agent-native orchestration frameworks such as LangGraph only where an agent graph is actually needed.
NEXUS problem: long-running research, approval waits, retries and connector interruptions need resumability and idempotency.
Acceptance direction: kill/restart during a synthetic multi-step workflow; require exactly-once consequential intent, no duplicate outreach/action, preserved approval state, deterministic recovery and auditable events.
Current position: research. Existing simple workflows stay simple until durable-execution need is measured.

### 3. Policy-driven agent evaluation
Candidate direction: policy/spec-driven evaluation frameworks such as ASSERT/ACS concepts, plus NEXUS-native adversarial suites.
NEXUS problem: generic benchmark PASS does not prove compliance with project isolation, authority, approval or provenance rules.
Acceptance direction: generate/evaluate cases directly from NEXUS invariants; require zero critical authority/approval/project-isolation escapes across frozen regression suites.
Current position: high-priority research because it strengthens every later agent/tool adoption.

### 4. Agent sandboxing / containment
Candidate direction: benchmark sandboxes by network isolation, filesystem isolation, credential boundaries, process isolation, observability, reset/rollback and policy enforcement rather than popularity.
NEXUS problem: coding/research workers need a place to fail without reaching company data or production.
Acceptance direction: adversarial escape suite with no secret/network/host leakage and full disposable reset.
Current position: design a NEXUS sandbox profile before selecting a product.

### 5. Provider/model gateway
Candidate: OmniRoute under the already-defined governed sandbox contract.
NEXUS problem: provider fragmentation, cost/latency variance and common benchmark surface.
Acceptance direction: explicit provider allowlist, no session-token providers, actual-provider traceability, sanitized prompts, three reproducible clean runs, rollback and measured benefit.
Current position: SANDBOX_EXPERIMENT only.

### 6. Observability / traces
Candidate direction: OpenTelemetry-compatible internal event schema, while treating changing GenAI semantic conventions as research input rather than authority.
NEXUS problem: compare models/agents/workflows on duration, cost, corrections, policy findings and outcomes without framework lock-in.
Acceptance direction: every experiment emits stable NEXUS event fields even if vendor/framework trace formats change.
Current position: build vendor-neutral event contract first.

## Infrastructure principle
NEXUS should become more replaceable, not more dependent: stable IDs, explicit schemas, event logs, provenance, adapters, frozen acceptance corpora and rollback contracts sit above any specific model, agent framework, memory database, router or orchestration product.

## Promotion rule
RESEARCH -> EXPERIMENT -> ADOPT_CANDIDATE -> separately approved implementation/merge/deploy. Promotion requires a repeated problem, evidence that the existing mechanism is insufficient, reproducible acceptance tests, project isolation, provenance, exact approval boundaries, measurable improvement and rollback.
