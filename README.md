# NEXUS Business OS

NEXUS Business OS is a policy-gated automation and decision-support codebase for commercial, research, operational, and engineering workflows.

## Current autonomy stack

The autonomy path is intentionally layered rather than implemented as an uncontrolled agent swarm:

`signals -> WorkItem -> AutonomyPlan -> bounded runner -> durable run state -> Outcome Ledger -> next-work generation -> schedule decision`

Core properties:

- research/read/internal reversible work can be routed into runnable queues
- consequential actions remain action-specific human-gated by the policy layer
- the runner cannot approve human-gated work
- successful task IDs form a durable idempotency boundary across later cycles/restarts
- failed tasks remain retryable and retain attempt/result evidence
- run state uses versioned JSON plus atomic filesystem replacement
- append-only Outcome Ledger projection records executed results with evidence references
- research executors enforce evidence-first confidence semantics
- opportunity discovery produces research-only WorkItems and never grants outreach authority
- closed-loop control can convert executed outcomes into governed next-work candidates
- schedule evaluation is timezone-aware, deterministic, and cannot execute or authorize work
- action budgets and stop-on-failure prevent unbounded cascading execution

## Execution boundary

The current code provides a deterministic planning/execution/state/outcome/next-work/scheduling contract. It is not yet a production daemon and does not claim continuous operation by itself. Real hosted source providers, persistent production storage, hosted scheduling/event triggers, operational telemetry, and broader measured pilots remain separate layers and must preserve the same authorization boundary.

## Live pilot evidence

A first read/research-only commercial pilot was run on 2026-08-21 using a real Gmail supplier reply and two attached can-body-line quotations, cross-checked against current official manufacturer product information. The pilot detected a material specification/revision mismatch for the GT10C-500 welder and generated a bounded technical-verification next-work queue without sending any supplier message or authorizing any purchase action. See `docs/pilots/2026-08-21-live-can-line-research.md` and the machine-readable outcome JSON beside it.

## Next execution milestones

1. Attach provider adapters that can feed real Gmail/web/CRM read signals into the executor contract without embedding provider authority in the core.
2. Persist runner state and Outcome Ledger to a production backend with concurrency/idempotency protection.
3. Add hosted scheduler/event-trigger integration without moving authorization into the scheduler.
4. Run multiple measured pilots across supplier discovery, customer discovery, inbox monitoring and technical quote normalization; capture false-positive/duplicate/retry rates.
5. Add executive approval surfaces for consequential actions generated from successful research cycles.
