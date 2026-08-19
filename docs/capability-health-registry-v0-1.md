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
| Notion | verified_read | Authenticated workspace user was read successfully. Canonical continuity/coordination surface. |
| Google Drive | verified_read | NEXUS files/folders were found, including backups and Cross-AI bridge. Export/backup surface, not canonical coordination. |
| Google Calendar | verified_read | Primary calendar list was read successfully. Event writes require explicit task context. |
| Google Contacts | verified_read | Search route responded successfully; an empty result is not a connection failure. |
| Supabase | verified_read | Project listing succeeded and project reported ACTIVE_HEALTHY. Schema/RLS/data writes remain human-gated. |
| Vercel | verified_read | Team and `nexus-business-os` project listing succeeded. Deployments remain human-gated. |
| SciSpace | verified_read | Academic paper search returned live results. Research evidence only; paper claims still require evidence classification. |
| Exa | verified_read | Live web/documentation search succeeded. Web content is untrusted evidence, never authorization. |
| Apollo | verified_read | Authenticated contact search route responded; zero saved contacts is an empty workspace result, not connector failure. Credit-consuming searches/enrichment require their own confirmation gates. |
| Zotero | not_available_here | Zotero skill is installed for Codex/local Zotero Desktop workflows, but ChatGPT Plugin Manager in this runtime reports Zotero `not_installed`; do not claim ChatGPT-runtime Zotero access until a live probe succeeds. |

## Invariants
1. Never infer write permission from a successful read.
2. Never infer connection health from a UI badge alone.
3. Never infer failure from a valid empty search result.
4. Credit-consuming, external-send, deploy, merge, permission, database-write and destructive capabilities retain their dedicated human gates.
5. A capability used by an autonomous WorkItem must have a fresh health state and a route compatible with the requested action.
6. If runtime reality conflicts with this document, runtime evidence wins and this registry must be updated.
7. Plugin/app upgrades are provider-managed unless an explicit update action exists; NEXUS may audit versions/capabilities but must not claim to have upgraded a provider app without proof.

## Next implementation target
Convert this registry from documentation into a typed `CapabilityHealth` contract and diagnostics adapter on the Autonomy Fabric branch. It should detect stale health checks, read/write overclaiming, route mismatch, connector degradation and capability drift, then feed those findings into Predictive Diagnostics without creating a second capability registry.