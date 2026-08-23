# NEXUS Critic Redesign v2

Status: shadow architecture proposal. This document does not authorize merge, deploy, external send, permission changes, production mutations or self-promotion.

## Critic verdict

NEXUS has accumulated strong safety, provenance and learning primitives, but the main risk has shifted from missing capability to coordination and state complexity. The system should not grow by adding more agents or frameworks by default. It should grow by improving the quality of a small number of shared primitives: canonical state, memory lifecycle, verification, recovery, architecture selection and outcome feedback.

## Research-backed redesign principles

1. **Single-agent is the default control architecture.** Multi-agent coordination is admitted only when task structure is measurably parallelizable and central verification is available. Nature Machine Intelligence (2026) reports large gains on parallelizable financial reasoning but degradations up to 70% on sequential planning, with coordination overhead and error amplification as first-order effects.
2. **Memory is a lifecycle, not a vector dump.** EverMemOS (ACL 2026) shows gains from episodic trace formation -> semantic consolidation -> reconstructive recollection. NEXUS should preserve raw evidence, consolidate stable knowledge, and reconstruct only necessary/sufficient context for a decision.
3. **Obsolete memory must be penalized, not merely retrieved.** Recent memory benchmarks show persistent reuse of invalidated memories. NEXUS therefore needs explicit validity intervals, supersession and selective forgetting at retrieval time while preserving raw history.
4. **State transitions must be verifier-backed.** Long-horizon agent research increasingly shows that explicit verified state, rather than raw growing trajectory context, improves progress tracking and recovery.
5. **Recovery is a first-class runtime capability.** AgentRewind (2026) shows that aligned checkpoints and rewind memory improve long-horizon task completion. NEXUS should checkpoint both reasoning state and controlled environment/action state where possible.
6. **LLM judges are advisory unless calibrated.** REFLECT (2026) reports overall accuracies below 55% for fine-grained research-agent failure detection. Deterministic checks, structured evidence and human validation must outrank monolithic judge scores.
7. **Verification should be decomposed.** Fine-grained rubric- and span-level verification is more reliable than a single holistic score on long trajectories. NEXUS should separate process, outcome, controllability and side-effect checks.
8. **Tool ecosystems require retrieval and replanning.** PlanBench-XL (2026) shows severe collapse when tools are blocked or recovery paths lengthen. Tool routing should retrieve the minimum relevant capability set, verify tool outputs and re-plan on silent failures.
9. **Self-improvement must be measured as failure avoidance.** Reflection that is not correctly diagnosed does not reliably improve future behavior. Lessons should be promoted only when future comparable failures measurably decline.

## Target architecture

### 1. Canonical Decision State

One project-scoped state object is shared by planner, researcher, executor and verifier:

- active goal and acceptance criteria
- canonical source refs and authority tiers
- verified requirements
- live evidence refs
- current unknowns and contradictions
- entity IDs and project IDs
- next-best-action candidates
- approval class
- outcome target
- rollback checkpoint

No agent may create an independent truth store.

### 2. Dual-speed Memory OS

**Fast path:** append immutable events/evidence and lightweight episodic traces.

**Slow path:** consolidate only after a semantic/project boundary or verified state change. Consolidation produces stable semantic records with provenance, validity interval and supersession links.

**Read path:** hybrid retrieval:

- semantic similarity for local recall
- entity/project/temporal/causal traversal for structurally relevant evidence
- explicit contradiction and supersession expansion
- evidence-budget pruning before model context assembly

Raw evidence is never deleted by consolidation.

### 3. Architecture Selector

Before creating workers, classify task structure using measurable properties:

- parallelizable fraction
- sequential dependency
- tool count
- context degradation
- verification availability
- latency/cost priorities

Default: single agent. Parallel research uses bounded workers plus one verified synthesis point. Centralized multi-agent is reserved for contexts where single-agent utilization is demonstrably degraded and decomposition is real.

### 4. Verification Stack

Order of preference:

1. deterministic oracle / executable check
2. structured evidence verifier
3. calibrated specialized verifier / rubric decomposition
4. human review for consequential, external or irreversible actions
5. LLM holistic judge only as advisory signal

No self-reported DONE state may update canonical state.

### 5. Recovery and Rewind

Each bounded generation should maintain:

- checkpoint ID
- canonical state digest
- action/environment references that can be restored or compensated
- failure diagnosis
- prior-attempt summary
- retry budget

On failure: targeted recovery first, full restart only when local repair cannot restore invariants.

### 6. Outcome-Coupled Learning

Learning unit:

Evidence -> Decision -> Action -> Outcome -> Failure/Success attribution -> Lesson -> Candidate change -> Replay -> Failure Avoidance Rate -> Promotion decision.

A lesson is not considered learned because it was written to memory. It must be retrieved in a comparable future task and reduce recurrence without introducing safety or outcome regressions.

## Project-wide speed redesign

- Retrieve tools and context on demand instead of exposing every tool and every historical record to every run.
- Keep synchronous fast path limited to canonical-state lookup, authority check, high-recall evidence retrieval and immediate verification.
- Move graph consolidation, deduplication, index repair and long-form research synthesis to bounded asynchronous generations when a runtime exists.
- Cache stable canonical structures by version/hash; never cache dynamic commercial facts without expiry.
- Prefer targeted repair to full replanning.
- Use parallelism only for independent evidence collection and merge through one verifier-backed synthesis point.
- Measure latency as p50/p95 decision time, not only total task success.

## Required project metrics

Technical:
- source-authority violation rate
- cross-project contamination rate
- stale-memory use rate
- contradiction detection recall
- verifier false-positive/false-negative rate
- tool silent-failure detection rate
- retry/recovery success rate
- p50/p95 decision latency
- tokens and tool calls per accepted decision

Commercial:
- qualified opportunity precision
- duplicate outreach rate
- RFQ-to-quote conversion
- quote-to-negotiation conversion
- negotiation-to-order conversion
- gross margin per closed opportunity
- time-to-qualified-decision
- human override rate

Learning:
- failure avoidance rate on replayed comparable cases
- lesson retrieval hit rate
- negative-transfer rate
- regression introduction rate

## Current canonical-source alignment as of 24 Aug 2026

- NEXUS Master Context v1.4 is project-wide canonical operating guidance.
- Source Registry v1.1 governs stable authority selection.
- Hydrotester Engineering Master v1.1 supersedes v1.0.
- Heat Treatment Master v1.1 is canonical with a throughput revalidation hold; ~40 pipes/hour is working state, not a final contractual fact.
- KCl Acceptance Master v1.0 and Can Forming Master v1.0 remain canonical.
- Dynamic prices, contacts, availability, project status, law and commercial terms require live refresh.

## Anti-patterns now explicitly rejected

- more agents by default
- all tools visible to all workers
- one giant shared context as memory
- vector similarity as the only memory access path
- monolithic LLM judge as promotion authority
- retry loops without diagnosis
- global restart for local recoverable failure
- final answer or worker consensus treated as verified state
- benchmark improvement without matched cost/compute accounting
- architecture growth without outcome or reliability improvement

## Promotion criterion for this redesign

The redesign may progress beyond shadow only if it beats the current baseline on a matched replay suite without weakening safety gates. Required evidence should include architecture-selection correctness, source-authority correctness, stale-memory rejection, verifier reliability, recovery success, latency/cost deltas and at least one real commercial workflow outcome trace.

## Research anchors

- EverMemOS: ACL 2026, https://aclanthology.org/2026.acl-long.2125/
- Capable language models can outgrow the benefits of collaboration: Nature Machine Intelligence 2026, https://www.nature.com/articles/s42256-026-01268-y
- PlanBench-XL: arXiv 2606.22388
- AgentRewind: arXiv 2608.14380
- REFLECT: arXiv 2605.19196
- BenchTrace: arXiv 2605.29225
- Holistic Evaluation and Failure Diagnosis of AI Agents: arXiv 2605.14865
