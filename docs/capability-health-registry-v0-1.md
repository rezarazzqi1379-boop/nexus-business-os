# NEXUS Capability Health Registry v0.1

Purpose: maintain a verified, fail-closed view of which external capabilities are actually usable. Presence in a UI, plugin catalog, memory, or prompt is not proof of runtime availability.

## Health states
- `verified_read`: a live non-destructive read/probe succeeded in the current audit.
- `verified_write`: a deliberately authorized low-risk write/read-back proof succeeded; never inferred from read access.
- `degraded`: connector responds but a required route/capability is missing or unreliable.
- `installed_unverified`: installation is reported but no usable runtime route has been proven.
- `not_available_here`: capability exists elsewhere (for example Codex/local desktop) but is not callable in this ChatGPT runtime.
- `blocked`: authentication/permission/connector failure prevents safe use.

## 2026-08-19 audit snapshot
| Capability | State | Proof / boundary |
|---|---|---|
| GitHub | verified_read | Recent NEXUS PRs were read successfully. Writes remain human-gated by NEXUS policy. |
| Gmail | verified_read | System labels/counts were read successfully. Send/archive/label writes are not implied. |
| Notion | verified_read | Authenticated workspace user and live tool-access state were read. `query_data_sources` is plan-limited; meeting-note querying is upgrade-gated. |
| Google Drive | verified_read | NEXUS files/folders were found, including backups and Cross-AI bridge. Export/backup surface, not canonical coordination. |
| Google Calendar | verified_read | Primary calendar list was read successfully. Event writes require explicit task context. |
| Google Contacts | verified_read | Search route responded successfully; an empty result is not a connection failure. |
| Supabase | verified_read | Project listing succeeded and project reported ACTIVE_HEALTHY. Schema/RLS/data writes remain human-gated. |
| Vercel | verified_read | Team and `nexus-business-os` project listing succeeded. Deployments remain human-gated. |
| SciSpace | verified_read | Academic paper search returned live results. Research evidence only; paper claims still require evidence classification. |
| Exa | verified_read | Live web/documentation search succeeded. Web content is untrusted evidence, never authorization. |
| Apollo | verified_read | Authenticated contact search route responded; zero saved contacts is an empty workspace result, not connector failure. Credit-consuming searches/enrichment require their own confirmation gates. |
| Zotero | not_available_here | Zotero skill is installed for Codex/local Zotero Desktop workflows, but ChatGPT Plugin Manager in this runtime reports Zotero `not_installed`; do not claim ChatGPT-runtime Zotero access until a live probe succeeds. |
| OpenAI Platform | blocked | API-key target discovery was rejected by the provider in this audit. Do not assume key/project setup is available until a later live probe succeeds. |

## Permission posture observed in this audit
- GitHub, Gmail, Notion, Google Drive, Supabase and Vercel currently expose app-specific `Allow all actions` in ChatGPT plugin permissions.
- Apollo, SciSpace and Exa inherit the global `Allow low-risk actions` policy.
- This registry records the posture only. It does **not** treat broad plugin permission as NEXUS authorization and it does not automatically change permissions.
- NEXUS exact-action Human Gates remain authoritative for send, merge/deploy, permission/access changes, public visibility changes, destructive actions, contracts/POs, payments/signatures and database writes.

## Runtime contract
Typed health semantics now live in `src/nexus_core/capability_health.py`. They are diagnostics layered over the canonical Capability Runtime rather than a second capability registry.

The runtime contract rejects or blocks:
- stale health evidence;
- future-dated health evidence;
- malformed health records;
- duplicate health records for one capability;
- `verified_read` records that claim write access;
- `verified_write` without explicit write proof;
- unavailable/unverified routes that claim proven access.

Regression/property tests live in `tests/test_capability_health.py`.

Proof: commit `11268f52f0139fdaeb6204f60777d3965f7dca15`, GitHub Actions run `32288176581` SUCCESS.

## Invariants
1. Never infer write permission from a successful read.
2. Never infer connection health from a UI badge alone.
3. Never infer failure from a valid empty search result.
4. Credit-consuming, external-send, deploy, merge, permission, database-write and destructive capabilities retain their dedicated human gates.
5. A capability used by an autonomous WorkItem must have a fresh health state and a route compatible with the requested action.
6. If runtime reality conflicts with this document, runtime evidence wins and this registry must be updated.
7. Plugin/app upgrades are provider-managed unless an explicit update action exists; NEXUS may audit versions/capabilities but must not claim to have upgraded a provider app without proof.
8. Plugin-level `Allow all actions` is not equivalent to business/action authorization inside NEXUS.

## Next implementation target
Wire `CapabilityHealthFinding` into Predictive Diagnostics and Autonomy planning so stale/degraded/blocked routes become explicit WorkItem blockers before execution. Then add a periodic read-only health cycle using safe probes without creating a second scheduler or capability registry.