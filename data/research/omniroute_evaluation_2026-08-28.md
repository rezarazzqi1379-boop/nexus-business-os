# OmniRoute evaluation — 2026-08-28

Status: INTERNAL RESEARCH / SANDBOX CANDIDATE. Not installed. No credentials connected. No production routing authorized.

## Source-derived facts / upstream claims
- Repository: `diegosouzapw/OmniRoute`, reviewed at release branch `release/v3.8.50`.
- License: MIT.
- Upstream README claims v3.8.50 catalogs 352 providers and 1,312 unique chat model IDs.
- Supports OpenAI-compatible clients and documents integrations with Claude Code, Codex, Cursor, OpenCode and others.
- Upstream documents MCP and A2A support, local/self-host deployment, routing/fallback and token compression.
- Security documentation states sensitive SQLite data can use AES-256-GCM when `STORAGE_ENCRYPTION_KEY` is configured; plaintext passthrough exists when that key is absent.
- Security documentation explicitly describes built-in guardrails as fail-open and prompt-injection detection as best-effort, not a complete firewall.
- The free-tier documentation states ToS flags are advisory and are not global routing gates. Some catalogued providers have proxy/automation/personal-use cautions.

## NEXUS classification
OmniRoute is not a new authority, Executive Kernel, policy engine or project router. Its potentially valuable role is narrower:

`NEXUS Resource Router / Provider Economy -> governed OmniRoute gateway adapter -> allowlisted provider/model -> measured result -> NEXUS Arena/Adoption Gate`

Potential benefit:
- reduce provider-specific integration work;
- broaden model/provider availability;
- supply fallback and quota telemetry;
- create one benchmark surface for OpenCode/Codex/other coding workers.

Material risks:
- provider-specific terms and free-tier claims change frequently;
- web-cookie/session-token or personal-use providers may be inappropriate for business use;
- upstream ToS warnings are informational rather than enforced by routing;
- provider fallback can silently change data destination unless NEXUS constrains every eligible target;
- upstream guardrails cannot replace NEXUS exact-action and ingress policy;
- credentials and prompts can traverse external providers during live use.

## Experiment contract
1. Pin exact release/image digest; do not use floating latest.
2. Self-host only for first experiment.
3. No real company secrets, supplier quotes, credentials, personal data or canonical documents in prompts.
4. Disable web-cookie/session-token providers.
5. Start with a tiny explicit allowlist of independently verified API/OAuth/local providers.
6. Disable autonomous fallback unless every fallback target is on the same allowlist and has verified terms/data policy.
7. Record the actual provider/model selected for each call.
8. Disable prompt/response logging at the NEXUS adapter where possible; never rely on router logs as canonical evidence.
9. Run the same frozen coding/research task through the current NEXUS route and OmniRoute route.
10. Evaluate with existing NEXUS Arena/Adoption Gate: correctness, policy violations, security findings, regressions, cross-project contamination, human corrections, duration and cost.
11. Require at least three reproducible clean runs and tested rollback before promotion.

## Current decision
`SANDBOX_EXPERIMENT`.

Reason: high potential value as a provider gateway, but current upstream breadth/free-tier claims do not by themselves justify connection to company data or credentials. A NEXUS-specific compliance/provider allowlist must exist first.

Rollback: remove the adapter and route model calls directly through the existing Resource Router/Provider Economy path.
