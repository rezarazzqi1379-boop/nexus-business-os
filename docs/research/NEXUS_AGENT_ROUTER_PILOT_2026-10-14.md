# NEXUS Agent Router Pilot v0.1

State: code and unit tests committed on isolated branch; tests NOT independently executed.

This is a standard-library-only synthetic proof of up to three concurrent read-only workers. It validates task/project scope and fails closed on non-read-only action kinds and approval_required requests. It neither installs agents nor contacts providers. It is NOT a replacement for the existing supervisor, project_control_plane, AutonomyStore, ApprovalStore, project_memory or nexus_chat_bootstrap.

Run in a checked-out project Windows clone: `.venv/Scripts/python.exe -m unittest tests/test_agent_router_pilot.py`. Then run the relevant regression suite. Inspect the current project APIs before integrating.

Missing: persistent queue and lease recovery, real idempotency, crash/restart tests, cross-process and cross-chat execution, UI, cost/token budgets, verified speedup and any actual external agent invocation. The boolean approval_required is a deny-only guard, not authorization; never treat it as an approval grant. Thread-based concurrency may not accelerate CPU-bound work. No external side effects are allowed.

Acceptance before any adoption: ten repetitions, isolation and approval tests, reproducible sequential-vs-parallel benchmark, forced restart and replay, exact evidence locators, bounded budget, rollback and independent test evidence. Authority Registry/Master reconciliation remains HOLD for consequential commercial tasks.

No merge, deploy, access expansion, external communication or production promotion authorized by this pilot.
