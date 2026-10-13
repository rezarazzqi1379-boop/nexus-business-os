# NEXUS Coordination Contract v1

Status: IMPLEMENTED / PENDING CI

## Purpose
Coordinate projects, chats, agents, prompts, tools and evidence without creating a second source of truth.

## Authority
Source Registry selects authority. Canonical project master governs stable project facts. Dynamic facts require live refresh. Chat/session memory is continuity only. Agent/plugin output is evidence/candidate output, never authority by itself.

## Four state scopes
1. CANONICAL — registry/master/approved decision records.
2. SHARED — tested repo contracts, decision log, capability census, failure/winning patterns.
3. SESSION — current plan, working hypotheses, temporary context.
4. EPHEMERAL — tool output/cache/transient reasoning.

Promotion is one-way only after evidence + acceptance test. SESSION/EPHEMERAL cannot silently overwrite CANONICAL.

## Direction Guard
Before consequential work verify project ID, registry/master, decision version, exact repo HEAD and live CI. Cross-project context fails closed.

## Pivot Lock
A change to project objective, canonical requirement, approval boundary or architecture decision creates a new decision version and requires reconciliation before execution. No silent prompt-only pivot.

## Portable Handoff Capsule
Across chat/model/agent boundaries persist only:
project_id; objective; exact tested HEAD/CI; evidence refs; decisions; unknowns; blocker; next safe action; protected-action flag.
A stale HEAD or missing evidence makes the capsule non-resumable.

## Context budget
Prefer progressive disclosure: stable authority summary → task-relevant evidence → raw source only when needed. Do not stuff all chats into every prompt. Deduplicate repeated context and retain source locators.

## Agent coordination
Central state is mediated by NEXUS; agents do not promote each other's claims. Parallelize independent reads/research/tests. Serialize tightly coupled writes. Every worker returns evidence refs, uncertainty, failure and measurable delta.

## Evaluation
Record prompt/skill/tool/model version where available; test cross-project isolation, stale CI, stale handoff, pivot drift, memory-as-authority and protected-action gating.

## External patterns studied
Microsoft multi-agent memory: memory != knowledge base; scope/governance.
Agent Harness: Native/Portable/Audited continuity; contract/events/capsule.
kode:harness: Direction Guard, Pivot Lock, shared vs local state.
agentevals: offline trace evaluation.
These are pattern donors, not NEXUS authority or automatically installed runtimes.
