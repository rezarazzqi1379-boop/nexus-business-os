# NEXUS Core Consolidation Plan v0.1

Status: REVIEW / CONSOLIDATION CHECKPOINT
Date: 2026-08-22

## Why this exists
NEXUS has accumulated multiple useful but overlapping draft branches. The current bottleneck is no longer lack of capability; it is integration cost, authority drift, review complexity, and the risk of promoting large experimental stacks before measured business loops exist.

This plan defines the smallest canonical Core and a disposition for the major open PRs reviewed on 2026-08-22.

## Canonical Core boundary

`Evidence -> Authority/Entity Resolution -> Decision -> Exact Action Approval -> Execution -> Outcome -> Learning`

Core owns only cross-domain invariants:
- provenance and epistemic class preservation
- authority/supersession rules
- project/entity isolation
- deterministic validation and fail-closed behavior
- exact-action human approval for consequential actions
- idempotency / duplicate-action controls
- compact privacy-first audit metadata
- outcome measurement contracts

Domain-specific qualification logic remains in vertical modules such as Hydrotester and Can Forming.

Agent runtimes, research meshes, self-improvement kernels, hosted schedulers, and additional frameworks remain experimental until measured NEXUS outcomes justify promotion.

## PR disposition map

### PR #29 — Align hydrotester authority with buyer Rev.1.2
Disposition: KEEP / DOMAIN-CANONICAL CANDIDATE

Why:
- preserves historical v0.1 instead of rewriting it in place
- records Rev.1.2 as a new authority revision
- latest basis currently recorded: WT 6-20 mm, length 9-12 m, 60 pipes/hour
- keeps test-pressure envelope and end/sealing condition as buyer blockers
- downgrades stale supplier matches
- current head includes fail-closed readiness hardening for unknown/pending statuses
- current CI is green

Do not merge solely because CI is green. Review authority evidence and domain semantics first.

### PR #28 — Deterministic Capability Governor
Disposition: KEEP / SMALL STANDALONE CONTROL MODULE

Why:
- small and bounded
- no network/model/external action authority
- hard gates prevent score-based automatic production adoption
- CI green at reviewed head

Constraint: the score remains heuristic. Capability promotion still requires measured NEXUS outcomes.

### PR #24 — P0 Benchmark Pair / Authority + Outcome Proof
Disposition: EXTRACT, DO NOT MERGE AS-IS

Keep/extract:
- A0-A8 authority model
- fail-closed supersession contract
- maturity stages
- benchmark observation contract
- Can Forming replay and scope-equivalence controls
- no-fake-precision measurement rules

Supersede/remove before promotion:
- Hydrotester edits that mutate `hydrotester_qualification_matrix_v0_1.json` in place
- Hydrotester dimensions/authority that predate Rev.1.2

PR #29 is the newer Hydrotester authority path. A consolidated benchmark branch should consume the new matrix rather than rewriting history.

### PR #18 — Per-send outreach approval hardening
Disposition: P0 EXTRACT TO CORE SECURITY

Invariant to preserve:
- approval of an initial external message must not pre-authorize a future follow-up
- planned follow-ups are data/plans only until an exact action-specific approval exists at execution time

This security property should not remain hostage to the full PR #13 autonomy stack.

### PR #12 — Security Policy + Threat Model
Disposition: KEEP / CORE GOVERNANCE CANDIDATE

Why:
- small, documentation-only, independent
- defines external/model/tool content as untrusted data rather than authorization
- codifies fail-closed behavior and exact-action human approval
- creates a stable security review context

### PR #10 — Privacy-first Audit Event Envelope
Disposition: KEEP IDEAS / EXTRACT AFTER EVALUATION DEPENDENCY REVIEW

Preserve:
- compact metadata-only audit events
- timezone-aware timestamps
- stable IDs and parent checks
- exact action refs for approval/action events
- no free-form sensitive payload
- Unicode/control-character hardening

Do not duplicate this with a second trace/observability framework.

### PR #13 — Autonomy Fabric
Disposition: INCUBATOR / SUPERSEDE AS MERGE UNIT

Reason:
- valuable source adapters, planning rules, checkpoint semantics and research-only boundaries exist
- but the PR has grown into a very large stacked merge unit
- security-critical pieces should be extracted independently
- measured business loop evidence is still insufficient to justify merging the entire fabric as Core

Do not add more unrelated capabilities to this PR.

### PR #17 — Autonomy Runner
Disposition: INCUBATOR / EXTRACT LATER

Potentially valuable primitives:
- bounded action budget
- stop-on-failure
- fail-closed missing executors
- durable versioned state
- idempotency semantics
- scheduler without action authority
- append-only outcome projection

Promotion gate:
- first stabilize Core security/authority contracts
- then benchmark one real read/research loop against a simpler deterministic implementation
- do not treat CI as proof of hosted 24/7 autonomy or business value

### PR #19 — Agent Evolution Kernel
Disposition: WATCH / DEFER

Self-improvement machinery is premature until NEXUS has repeated measured loops and a stable baseline. Keep as experiment evidence, not Core dependency.

## Immediate consolidation order

1. Finish independent review of PR #29; keep historical authority immutable.
2. Extract PR #18 exact-send approval invariant into a small Core-oriented branch.
3. Rebuild the useful portions of PR #24 on top of current main + PR #29 semantics without modifying historical Hydrotester files.
4. Keep PR #28 standalone; no automatic adoption authority.
5. Adopt one security policy/threat-model source rather than parallel security documents.
6. Treat PR #13/#17/#19 as incubators and stop adding new Core responsibilities to them.
7. Measure two real procurement loops before promoting a hosted agent runtime.

## Merge discipline

A candidate change may be considered Core only when all are true:
- one clear responsibility
- explicit source/authority semantics
- fail-closed malformed input behavior
- adversarial tests for the relevant failure mode
- no cross-project state leakage
- no new authorization path
- exact CI evidence at the reviewed head
- no unresolved overlap with a newer or smaller canonical implementation
- maturity claim limited to what the evidence proves

## Non-goals

This consolidation does not:
- merge any PR automatically
- deploy production code
- send external messages
- change permissions
- modify Supabase production state
- claim business ROI from unit tests
- add another agent framework

The purpose is to reduce the project to a reviewable, measurable Core while preserving useful experimental work for later extraction.