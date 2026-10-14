# NEXUS platform candidate assessment — 2026-10-13

Status: RESEARCHED / NOT INSTALLED / NO DEPLOYMENT. Project lane PRJ-STEEL-SALES, PR #111 draft. Avoid adding tools until a measurable repeated problem and acceptance test justify them. Existing repo already includes `deep_search_fabric.py`, `research_lab.py`, `system_capability_registry.py`, `nexus_connector_control_plane.py`, `self_improvement_runtime.py`, `market_intelligence.py`, `tests/` and `evals/` (observed on main root listing). Inspect existing functionality before selecting replacement.

| Candidate | Upstream | Potential value | Overlap / risks | Decision / admission test |
|---|---|---|---|---|
| GPT Researcher | https://github.com/assafelovic/gpt-researcher | Multi-source research with citations; web/local document input; optional MCP | Duplicates existing research fabric, LLM/API costs, external source reliability, possible leakage | EVALUATE ONLY. Offline benchmark of 10 existing steel tenders vs current pipeline; measure primary-source precision, duplicate rate, latency, cost; no installation until improvement is demonstrated |
| Langfuse | https://github.com/langfuse/langfuse | LLM traces, prompt versions, datasets and evals | Existing observability/evals, sensitive commercial data, self-hosting overhead; upstream docs note self-hosted telemetry defaults | EVALUATE ONLY. Synthetic local trace POC, redact PII, verify no outbound telemetry, compare cost/complexity with current audit pipeline |
| Activepieces | https://github.com/activepieces/activepieces | Workflow automation and MCP-compatible pieces | Existing automation/scheduler, connector permission and secret handling, risk of duplicate outreach | DEFER. Demonstrate one read-only evidence-ingestion workflow with idempotency and zero external writes; only then consider isolated install |
| Railway / Render | ChatGPT plugin directory (available but not installed in observed plugin search) | Managed hosting and logs | Hosting spend, production surface, deployment approvals | NO INSTALL/DEPLOY. Need deployment necessity, rollback, cost ceiling and exact approval |
| Vercel / monday.com | Installed connectors in plugin catalog at observation | Existing hosting/task capabilities | Do not infer any NEXUS app is deployed or board configured | READ-ONLY capability check if measurable workflow requires them; no live writes without approval |

## Security and governance acceptance checklist

1. Verify upstream repository, release/tag, maintainer, license, dependencies, CVEs and permission scopes at install time. A GitHub repository is not a trusted dependency by itself.
2. Pin a specific release or commit, record SHA/checksum and SBOM; scan dependencies and license constraints.
3. Run sandboxed, network-disabled or allowlisted smoke test on synthetic data with no production secrets.
4. Compare baseline vs candidate on identical evidence set; record precision, deduplication, cost, runtime and failure modes.
5. Require fail-closed approvals, idempotency, audit logs, rollback and a negative test proving no outreach/CRM writes.
6. Promote DESIGNED -> IMPLEMENTED -> TESTED only with evidence; MERGED, DEPLOYED and PRODUCTION are separate states.

## Decision

First implement the existing buyer-signal deduplication and deadline-conflict tests on PR #111. The highest-value potential external pilot is GPT Researcher for read-only primary-source discovery, but its benefit is a HYPOTHESIS until benchmarked. No platform has been installed, connected, deployed or paid for by this assessment. No new buyer or tender is claimed.

Sources: upstream project repositories listed above, plus GitHub PR #111 and its evidence intake protocol. Source Registry/master v1.8/v2.1 are historical baselines; check for supersession before promotion.
