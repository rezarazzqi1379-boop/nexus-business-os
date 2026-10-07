# LIVE CAPABILITY OVERLAY — 2026-10-07
Status: MEASUREMENT / DOES NOT SUPERSEDE SOURCE REGISTRY

Canonical Source Registry v1.8 remains the authority index and records capability state as of its effective period. Dynamic connector health must be refreshed before consequential use.

## Apollo
Registry historical state: NOT INSTALLED / NOT CALLABLE.
Live measurement 2026-10-07: connector callable. Read-only People API Search invocation reached Apollo but returned API_INACCESSIBLE on current Free plan.
Resolution:
- CONNECTOR_REACHABLE = true
- PEOPLE_SEARCH_AVAILABLE = false on tested plan/endpoint
- PAID_ENRICHMENT = not tested / not authorized
- OUTREACH = not authorized
Do not rewrite canonical registry merely to reflect a transient connector/plan state. Recover this overlay then refresh live.

## GitHub
Live measurement: repository and PR #105 readable/writable on working branch; exact-head CI is used for maturity binding.
Green CI does not imply merged, deployed or production.

## Rule
Capability state is temporal:
REGISTRY_BASELINE + LIVE_OVERLAY + TASK-SPECIFIC_PROBE.
Connected != authenticated for every action.
Authenticated != endpoint entitled.
Endpoint entitled != action approved.
