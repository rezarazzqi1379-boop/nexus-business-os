# GPT Researcher — cloud activation checklist v1 (2026-10-13)

Status: PREPARED, NOT INSTALLED, NOT DEPLOYED. NEXUS lane PRJ-STEEL-SALES, PR #111 Draft.

## Exact upstream pin
- Repository: https://github.com/assafelovic/gpt-researcher
- Release: v3.7.0 (2026-09-26)
- GitHub tag commit: `0957c301ed06c2a5857b834358c7227c739041d4` (observed live on 2026-10-13).
- Pin is an identity reference only, NOT a vulnerability audit or verification of all transitive dependencies.

## Host choice and access
- Existing connected Vercel project `nexus-business-os` (`prj_OoFE0HyWZugdCjv0WHCZvHG47InM`) is **not** an approved GPT Researcher worker host; do not modify it.
- Railway/Render worker may be suitable but no service/account connection, billing authorization, worker size or region is verified.
- Start with ephemeral CI/offline sandbox, no public endpoint, no secrets, no persistent process. Test cloud provider only after exact scope and cost cap are approved.

## Security and cost gates
- No production data, no customer/CRM/Gmail access, no model keys, no paid search calls, no outbound messages.
- Block egress at the **infrastructure layer**; an in-process boolean guard alone cannot enforce a network firewall.
- Use non-root user, read-only filesystem when feasible, limited CPU/memory/disk/time, pinned dependencies, sanitized logs and disposable workspace.
- Cost estimate: hosting UNKNOWN until provider, region, resources and price are confirmed. API cost is zero only when no API is called. Zero-budget config is NOT proof that cloud infrastructure cannot incur costs.
- Kill switch: destroy ephemeral environment; for a future worker, disable service and revoke scoped secrets, preserving logs and rollback manifest.

## Test implementation status
- `tests/test_gpt_researcher_cloud_admission.py` defines a pure-Python offline admission contract and negative tests for wrong project, unpinned version, real data, secrets, egress, writes, nonzero budget and persistence.
- This is a **unit-test-only guard** and is not wired to deployment or external process execution. Do not claim cloud isolation or actual GPT Researcher installation from its success.
- Next: run exact-HEAD GitHub CI; review package dependencies; create disposable synthetic fixture runner; compare NEXUS baseline and pinned candidate. Only then request deployment approval.

## Final activation approval payload (not yet granted)
Must name: provider, team/account, project/service, region, container/image digest, compute/storage, network egress, secrets, data classification, duration/restart schedule, monthly budget ceiling, billing method, rollback owner and target commit. Without these: BLOCKED_FOR_DEPLOYMENT_APPROVAL.
