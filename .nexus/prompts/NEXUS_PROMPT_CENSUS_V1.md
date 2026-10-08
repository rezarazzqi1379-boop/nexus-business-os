# NEXUS Prompt Census v1 — Reversible Governance Record

Baseline: PR #105 HEAD b315d398b8cc2bfa5f6adcc6f59927378c34d068 (CI #1308 success).
Scope: 25 files matching `.nexus/prompts/NEXUS_CONTINUE_V10*.md`.
Status: IMPLEMENTED; exact-head CI and behavioral acceptance remain required.

## Decision
All 25 V10-series CONTINUE documents are **HISTORICAL_CYCLE_PROMPT** records, not simultaneously active system instructions. They are retained unchanged for audit, provenance and rollback. This classification is a **routing policy**, not proof that every historical technique is obsolete.

Active routing candidates (subject to regression):
1. Canonical Source Registry + project master: authority.
2. `NEXUS_GLOBAL_KERNEL_V1.md`: global governance.
3. `prompt_contract.py` Operator v3: structured execution.
4. `NEXUS_PROMPT_OS_REGISTRY_V2.md`: prompt lifecycle and capability selection.
5. One task-specific capability + project overlay; tool adapters are not authority.
6. Eval/action gate.

## Replacements and preserved learnings
- V10.4 route benchmark → `outcome_census.py`; preserve measured route outcomes.
- V10.7 relationship binder → `opportunity_recovery.py` and commercial conversion gates.
- V10.19 tender/OCDS → `procurement_event_chain.py`, `commercial_source_registry.py`, source diagnostics.
- V10.22–23 conversion/evidence yield → `commercial_output_closure.py`, evidence quality and eligibility/document checks.
- V10.24 adapter fabric → governed adapter admission; no tool is authority.
- V10.26 intelligence graph → typed evidence and project-scoped edges; no uncontrolled graph expansion.
- Remaining V10 prompts → archived experiment references; use their evidence only through project-scoped validation.

## Non-destructive retirement
No historical file is deleted or modified. Do not automatically concatenate V10 prompts into the active context. Recovery from an archived prompt requires a named capability gap, a measurable acceptance test, review of canonical conflicts, and a versioned replacement.

## Release gates
- Exact-head CI success, prompt registry and operator regressions.
- Negative test: archived prompt cannot override Source Registry, project master or action gate.
- Vertical benchmark: at least one source-bound commercial edge with a reproducible locator; report zero if none.
- No protected merge, deploy, external communication, paid credits or CRM mutation without exact approval.
