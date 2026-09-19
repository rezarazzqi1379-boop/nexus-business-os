# NEXUS Delegated Operator Integration v0.1 — 2026-08-28

## Purpose
Connect the live-evidence Access/Authority Registry to the existing NEXUS autonomy substrate without creating a second scheduler, approval system, database, or agent runtime.

## Routing contract
Work is routed through:

`durable work queue -> live access observation -> authority decision -> execute internal / refresh access / prepare exact approval / hold`

This module is intentionally routing-only. It does not execute connectors, consume approvals, send messages, deploy, mutate production, place orders, pay, or perform destructive actions.

## Freshness rule
Connector status is dynamic evidence. An access observation has an explicit observed time and maximum age. Stale observations route to `REFRESH_ACCESS` before authority is considered. This prevents a connector that worked yesterday from being silently treated as live today.

## Consequential-action rule
External communication, production changes, payment/order actions and destructive actions never become executable from connector capability alone. They route to `PREPARE_APPROVAL`, preserving the canonical exact-action approval boundary.

## Internal autonomy rule
Only live-verified reads and verified reversible internal writes may route to `EXECUTE_INTERNAL`. Irreversible work disguised as an internal write fails closed.

## Acceptance tests
- fresh verified read -> EXECUTE_INTERNAL;
- fresh verified reversible internal write -> EXECUTE_INTERNAL;
- irreversible internal write -> HOLD;
- external message / production change -> PREPARE_APPROVAL;
- stale or missing access -> REFRESH_ACCESS;
- blocked connector -> HOLD;
- observation connector-binding mismatch -> HOLD;
- timezone-naive freshness evidence -> HOLD.

## Next integration
After exact-head CI, bind this router to the existing AutonomyStore worker loop through an adapter rather than modifying the durable queue schema first. The adapter must preserve current lease ownership, retries, dead-letter behavior, budget controls and circuit breakers.
