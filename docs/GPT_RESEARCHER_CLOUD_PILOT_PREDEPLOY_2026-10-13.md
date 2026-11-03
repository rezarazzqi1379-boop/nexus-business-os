# GPT Researcher cloud pilot — predeployment assessment (2026-10-13)

Status: PREPARED / NOT DEPLOYED / NO CLOUD SPEND AUTHORIZED. Project: PRJ-STEEL-SALES; Draft PR #111. This file is not evidence of a running service.

## Verified live access
- Vercel connected account team: `team_g2dpWQM3gFhXay3IKOcaYqVT`, slug `rezarazzqi1379-6402s-projects`.
- Existing Vercel project: `nexus-business-os`, id `prj_OoFE0HyWZugdCjv0WHCZvHG47InM`. Discovery does NOT establish deployment health, cost, build compatibility or permission to change it.
- GPT Researcher GitHub upstream `assafelovic/gpt-researcher`, latest observed release tag `v3.7.0`, published 2026-09-26; release has no attached GitHub assets. Resolve immutable tag SHA, lock dependencies and review security before any installation.
- Existing NEXUS Draft branch CI 38388323281 SUCCESS on SHA `3e527cc5f800e7f0f32f71b05cf7ef9732c59062` (does not test this document).

## Hosting options and decision
- Existing Vercel project: DO NOT MODIFY. Potential future control-plane/UI only; serverless execution limits and long-running worker fit not established.
- New isolated container worker (Railway or Render): CONDITIONAL CANDIDATE, not connected or provisioned. Confirm plan, quotas, egress, persistent storage, worker restart, secrets, logs and billing first.
- Ephemeral sandbox/CI runner: FIRST CHOICE for synthetic no-secrets benchmark; use only preapproved bounded resources and no billable model calls. A GitHub Actions CI job is not a persistent background worker.

## Access, security and isolation
- No production keys, real email/CRM access, commercial files, network-wide permissions, or cross-project datasets.
- Read-only GitHub access to a pinned public upstream; separate ephemeral workspace; no privileged Docker, host mounts or unrestricted egress; redact logs; no incoming public endpoint.
- Outbound connections disabled except allowlisted package mirrors after package audit; no model/API keys, so research-quality benchmark must use fixtures/mocks and cannot claim live GPT Researcher performance.
- Fail closed on absent cost cap, unreviewed dependency, missing kill switch, unverified telemetry or cloud role.

## Cost model (no invented price)
- Hosting cost: UNKNOWN until exact region, plan, worker size, runtime and pricing are verified live.
- LLM and search API usage: zero for the synthetic offline pilot; live run cost UNKNOWN and requires separate approval.
- Network egress, storage, logs, build minutes: UNKNOWN; set hard limits and billing alerts before any provisioning.
- Approved budget: NONE for new spend. Do not infer free-tier eligibility or free capacity.

## Test plan and acceptance
1. Pin upstream commit SHA and verify manifest, license and dependencies.
2. Add an isolated benchmark adapter disabled by default; prepare ten synthetic steel-tender fixtures (deadline conflicts, expired notices, duplicate notices, fake hosts, wrong grade/width, aggregator-only leads).
3. Run current NEXUS baseline and candidate fixture/mocked path; record exact SHA, test counts, source-precision, false-positive promotion, dedup, runtime and cost (zero live API).
4. Require zero false VERIFIED_ACTIVE_BUYER, zero outbound action, no secrets, no unintended writes, and reversible teardown.
5. Only after passing and reviewing cloud provider pricing, request exact approval for provider, project/service name, region, size, budget cap, secrets, allowed egress, schedule and rollback.

## Approval and blockers
- User approved assessment/preparation, explicitly NOT deployment.
- Cloud host choice, service permissions, immutable upstream SHA, dependency security review, cost cap and live API credentials remain unresolved.
- No install, deployment, daemon, secret creation, payment or external outreach performed.
