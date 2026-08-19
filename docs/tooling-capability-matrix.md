# NEXUS Tooling & Capability Matrix v0.1

Verified: 2026-08-19

Purpose: extend NEXUS only where a real operational bottleneck exists. This file is not a shopping list for apps or agents. Every capability must justify itself through a measurable business or execution need.

## Design rule

Prefer one reliable capability over multiple overlapping apps. A new plugin, agent or service is added only when the current stack cannot satisfy a concrete need with acceptable reliability, auditability and effort.

## Current core stack

| Capability | Current system | Role | Status | Write policy | Current decision |
|---|---|---|---|---|---|
| Code/version/tests | GitHub | Canonical code, PRs, issues, CI | Available | Feature-branch writes may proceed; merge is human-gated | KEEP |
| Commercial evidence | Gmail | Supplier/customer communication evidence and drafts | Available | Drafting may proceed; external send is human-gated | KEEP |
| Human-readable operating state | Notion | Decisions, canonical map, research, relationship signals, outcomes, AI handoffs | Available | Reversible internal writes allowed; destructive cleanup gated | KEEP |
| Structured runtime/state | Supabase/PostgreSQL | Runtime rows and future deterministic sync | Blocked/degraded | No schema or adapter writes until read access and real schema are verified | REPAIR |
| Deployment | Vercel | Production/preview deployment surface | Available but current-code parity false | Production deploy is human-gated | KEEP |
| Primary-source research | Web / Exa | Current external verification and research | Available | Read/research only | KEEP |
| File/source workspace | Google Drive | Master documents, Sheets/Docs/Slides when needed | Available | Writes only when a specific workflow needs them | KEEP |
| Scheduling/contacts | Google Calendar / Contacts | Meetings, free-busy, contact resolution | Available | External calendar/contact mutations require task-specific approval | ON DEMAND |
| Professional relationship lookup | LinkedIn | Professional profile lookup where relevant | Available | Primarily read/lookup | ON DEMAND |

## Existing coded capabilities

1. Procurement evidence-to-outcome model.
2. Stable IDs, provenance and entity-consistency validation.
3. Evidence classification draft (`fact | claim | estimate | inference | hypothesis | assumption | unknown`).
4. Requirement Readiness Gate in shadow mode (`approved | provisional | unknown_blocking`).
5. GitHub CI for test execution.
6. Human-gated external action policy in the capability-runtime branch.
7. Evidence-backed capability registry/planner in the capability-runtime branch.

## New capability-runtime objective

The capability runtime is intentionally small. It does not execute arbitrary tools or create autonomous agents. It provides:

- a registry of what NEXUS can actually read/write;
- current status (`available`, `degraded`, `blocked`, `candidate`, `not_connected`);
- proof references for capabilities claimed as live;
- minimal routing from a declared need to an existing capability;
- surfacing of unresolved needs instead of silently inventing integrations;
- human-approval gates for external messages, merges, production deploys, access changes, deletion/archive, contracts/POs, payments and signatures.

## Plugin discovery — 2026-08-19

Installable plugins surfaced by current plugin search included Slack, Linear, Airtable, HubSpot, Monday.com, Todoist/TickTick and others. No direct n8n, Make, Zapier, WhatsApp or Telegram integration surfaced in the targeted plugin search.

### Current decisions

- **Airtable — DO NOT INSTALL NOW.** It would duplicate Notion + Supabase.
- **Linear — DEFER.** GitHub Issues + Notion already cover current software/project tracking. Install only if issue-flow complexity becomes a measured bottleneck.
- **HubSpot — DEFER.** Potentially valuable later for a larger sales/relationship pipeline, but premature while NEXUS is still proving the evidence-to-outcome loop and already stores relationship/outcome state in Notion.
- **Slack — DEFER.** Useful only if the operating team actually adopts Slack as a live coordination channel.
- **Monday.com — DO NOT INSTALL NOW.** Overlaps current coordination stack.
- **Todoist/TickTick — DO NOT INSTALL NOW.** Current task state belongs in NEXUS/Notion/GitHub; reminders can use native automation when explicitly required.

## Capabilities that are justified next

### 1. Supabase Access Recovery

Need: restore verified read access, inspect actual schema/grants/RLS, then map current GitHub models to live rows. This is a repair, not a new integration.

Success proof: harmless SQL succeeds, live tables/columns are retrievable, and at least one real case can be read back deterministically.

### 2. Proposal / Quotation Ingestion

Need: once supplier proposals arrive, extract specs, deviations, commercial terms and missing fields into a comparable structured record.

Build gate: begin only when there are enough real proposals to test against; do not build from synthetic documents alone.

### 3. Supplier Capability Evidence Ladder

Need: distinguish supplier statement from official product evidence, project-specific proposal, reference evidence and verified acceptance/performance without fake numeric confidence.

Current state: manual/shadow experiment only. Do not code into a production rule until current supplier cases show it improves qualification consistency.

### 4. Follow-up / Reply Watch

Need: surface new supplier replies and due follow-ups without auto-sending messages.

Implementation preference: native scheduled/conditional automation or Gmail-driven watch when available. External messages remain human-gated.

### 5. Engineering Requirement Authority Layer

Need: preserve which buyer requirement values are approved, provisional or unknown and link each approved value to an authority source.

Current state: Requirement Readiness Gate is implemented in shadow mode. Field validation is still required.

## Not justified yet

- multi-agent fleet;
- autonomous negotiation agent;
- automatic contract/PO signing;
- automatic production deployment;
- duplicate CRM/database;
- new dashboard solely for visibility;
- vector database/RAG layer without a measured retrieval failure;
- WhatsApp/Telegram automation without a stable supported connector and clear compliance/operational need;
- n8n/Make/Zapier layer merely to connect systems that the current control plane can already operate directly.

## Approval boundary

NEXUS may autonomously research, read, analyze, create drafts, create internal records, write reversible feature-branch code and run tests. Explicit human approval is required before external commercial sends, merges to production branches when consequential, production deploys, access/permission changes, destructive cleanup, contracts/POs, payments and signatures.
