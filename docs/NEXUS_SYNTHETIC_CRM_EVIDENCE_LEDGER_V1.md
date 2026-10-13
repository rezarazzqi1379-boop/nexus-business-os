# NEXUS Synthetic CRM Pilot — Evidence Ledger v1

- Scope: SANDBOX synthetic data only; no real company, contact, pricing or procurement evidence.
- Source: main commit `38ca97b5251b0866a939515a51a7fbb278dd24d5`.
- Pilot branch: `nexus/synthetic-crm-evidence-pilot-2026-10-13`.
- Maturity: IMPLEMENTED in Draft PR; TESTED only after a successful CI run on the exact branch HEAD.
- Synthetic opportunity: SANDBOX / ACCOUNT-1 / CONTACT-1 / OPP-1.
- Output: deterministic JSON-compatible record list and SHA-256 evidence digest.
- Negative checks: cross-project read/export attempt, duplicate opportunity, invalid IDs, invalid project.
- No live CRM operations, network calls, vendor installation, data synchronization, payments or outbound messages.
- Twenty CRM: RESEARCHED / NOT INSTALLED / NOT BENCHMARKED.
- EspoCRM: RESEARCHED / NOT INSTALLED / NOT BENCHMARKED.
- Comparison status: UNKNOWN. Do not rank vendors until pinned, isolated installs and identical acceptance tests succeed.
- Remaining acceptance gates: vendor license/security review, pinned dependencies, isolated install, synthetic CRUD/export, restart/rollback, resource measurement, evidence preservation, exact host authorization.
- Rollback: close Draft PR and delete its isolated branch only after separate approval; main remains unchanged.
