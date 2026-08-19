# NEXUS Current-State Architecture

Verified: 2026-08-19

This file is the code-repository current-state manifest. It does not replace the stable NEXUS Master Context; it records runtime changes that supersede older roadmap wording about what is already live.

## Source-of-truth split

- **ChatGPT / NEXUS HQ** — control plane, orchestration, analysis, execution when a connected tool supports the action. Not the sole memory store.
- **GitHub** — canonical source of truth for NEXUS code, tests, CI configuration, and version history.
- **Notion** — human-readable operational coordination, canonical-object map, decisions, relationship signals, outcome learning, and Cross-AI Handoff Log.
- **Gmail** — primary evidence for live commercial communications and supplier replies.
- **Supabase/PostgreSQL** — structured runtime/state store already implemented, but currently connector-degraded because even a minimal `select now()` returns a permission error. Do not infer live schema while access is degraded.
- **Vercel** — deployment layer. A production project is READY, but the existing deployment must not be assumed to contain the latest GitHub Vertical 01 code until a new deployment is explicitly verified.
- **Claude** — independent auditor/second opinion and occasional direct executor through the shared handoff layer; not a second source of truth.

## Vertical 01 maturity

Current main chain:

`Evidence -> Relationship -> Signal -> Opportunity -> Outcome`

Implemented in GitHub with stable IDs, provenance checks, entity consistency, outcome-state invariants, and real evidence-linked fixtures for SupplierTR, GH Petro, and YAXING.

Current maturity:

`Implemented in GitHub -> local structural validation passed -> GitHub Actions operational and verified on draft PR #1 -> Supabase adapter pending verified schema access -> not deployed as current Vercel runtime -> not production`

Verified CI proof: draft PR #1 (`feature/evidence-classification`) triggered GitHub Actions run `32243906968`; job `pytest` completed successfully, including checkout, Python setup, editable install and `pytest -q`.

Draft PR #1 is **not merged**. It proposes explicit epistemic evidence classes (`fact | claim | estimate | inference | hypothesis | assumption | unknown`) so supplier statements cannot silently become verified facts. Claude review remains pending.

## First measured loop proof

Notion now contains evidence-backed Relationship Signals for SupplierTR, GH Petro and YAXING, each linked to canonical Entity Registry entries and Gmail evidence.

A YAXING micro-outcome was also written to the canonical Outcome Ledger: technical engagement/catalog receipt progressed the route, but the next bottleneck was identified as buyer-side engineering data (final Hydrotester pipe-length and wall-thickness/ID range). This is an **Inconclusive / Retest** micro-outcome, not supplier qualification.

This is stronger proof than a structural fixture alone because Evidence -> Relationship Signal -> Opportunity/Next Action -> Outcome/Learning is represented against a live supplier interaction outside the code testbed.

## Current hard gates

1. No new agent/registry/framework/integration merely to create activity.
2. No Supabase adapter based on remembered or guessed schema.
3. No supplier is commercially qualified merely because a structural test fixture validates.
4. No final Hydrotester length/wall-thickness assumption until engineering confirms it.
5. No external consequential action without human approval.
6. No claim that current GitHub code is deployed on Vercel until deployment parity is verified.
7. No production AI-agent runtime before the first procurement loop is measurable and repeatable.
8. Draft PR #1 must not be merged only because CI passed; independent review and classification correctness still matter.

## Drift rules

- Stable project context can be older than runtime. Runtime facts must be re-verified before action.
- A newer verified GitHub/Notion/Gmail/Supabase artifact supersedes older narrative state only for the fields it actually proves.
- Backup pages are lineage snapshots, not live operating objects.
- Code maturity must always be stated as Designed / Implemented / Tested / Deployed / Production separately.

## Verified research decisions — 2026-08-19

### GitHub Actions

The NEXUS test workflow has `workflow_dispatch`, `pull_request`, main-push execution and explicit least-privilege `contents: read`. CI is now verified operational through PR run `32243906968`, which completed with conclusion `success`.

### Supabase security/access

Official Supabase documentation separates object grants from Row Level Security: grants determine whether a role can reach an object; RLS determines which rows it can access. Because the connector currently fails even on `select now()`, treat this first as an integration/role-permission failure rather than automatically rewriting table RLS policies. When access returns, inspect role/grants/RLS separately and use least privilege. Service-role or bypass-RLS credentials must never be exposed to a client.

### Future agent/runtime direction

Current agent-runtime direction stays deliberately small: manager/orchestrator + tools/specialist handoffs + guardrails + human gate + tracing/evaluation. No large agent fleet before measurable closed-loop value. Sensitive trace/model payload capture should default off for commercial data, and internal event contracts should remain portable rather than being coupled to evolving telemetry conventions.

### Hydrotester feasibility research

Official manufacturer material supports technical credibility of the 120 MPa class, but not compliance of any specific offered machine. Marley independently asked for pipe-length and wall-thickness ranges before quotation. Final Hydrotester geometry therefore remains a decision-critical internal engineering blocker.

### Future Signal Registry canonicalization

`NEXUS Future Signal Registry` at `5f728db4-2dfb-4ece-9c80-29707a118383` / `collection://ae665f6a-e726-4936-8e31-2b67e45b7ba9` remains the canonical write target. A unique source-less regional logistics Watch item from sibling `65efe565...` was re-researched against current IMO evidence, corrected at source, and merged into the canonical registry. The sibling remains lineage/recovery and should receive no new writes.

## Near-term proof targets

1. Receive Claude KEEP/CHANGE/STOP review of draft PR #1 / Vertical 01 evidence classification.
2. Restore Supabase read access; inspect integration role/grants/RLS before changing policies or code.
3. Obtain Hydrotester pipe-length and wall-thickness/ID range from engineering and advance Marley / Yedi Mavi / ANZ without specification drift.
4. Record the next supplier reply/quote/referral as a measured outcome and compare expected vs actual Next Best Action.
5. Verify Vercel deployment parity only when a deliberate deployment is justified; do not deploy merely to show activity.
6. Only after repeated loop proof, start Proposal Ingestion / deviation extraction v0.2.
7. Produce one final Work-migration parity checkpoint before changing orchestration surface.
