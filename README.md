# NEXUS Business OS

NEXUS Business OS is a policy-gated automation and decision-support codebase for commercial, research, operational, and engineering workflows.

## Current autonomy stack

The autonomy path is intentionally layered rather than implemented as an uncontrolled agent swarm:

`signals -> WorkItem -> AutonomyPlan -> bounded runner -> durable run state -> schedule decision`

Core properties:

- research/read/internal reversible work can be routed into runnable queues
- consequential actions remain action-specific human-gated by the policy layer
- the runner cannot approve human-gated work
- successful task IDs form a durable idempotency boundary across later cycles/restarts
- failed tasks remain retryable and retain attempt/result evidence
- run state uses versioned JSON plus atomic filesystem replacement
- schedule evaluation is timezone-aware, deterministic, and cannot execute or authorize work
- action budgets and stop-on-failure prevent unbounded cascading execution

## Execution boundary

The current code provides a deterministic planning/execution/state/scheduling contract. It is not yet a production daemon and does not claim continuous operation by itself. Real source executors, hosted scheduling/event triggers, Outcome Ledger integration, operational telemetry, and measured pilots remain separate layers and must preserve the same authorization boundary.
