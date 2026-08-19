# NEXUS Current-State Architecture

Verified: 2026-08-19

This file is the code-repository current-state manifest. It does not replace the stable NEXUS Master Context; it records runtime changes that supersede older roadmap wording about what is already live.

## Source-of-truth split

- **ChatGPT / NEXUS HQ** — control plane, orchestration, analysis, execution when a connected tool supports the action. Not the sole memory store.
- **GitHub** — canonical source of truth for NEXUS code, tests, CI configuration, and version history.
- **Notion** — human-readable operational coordination, canonical-object map, decisions, relationship signals, outcome learning, research/experiments, and Cross-AI Handoff Log.
- **Gmail** — primary evidence for live commercial communications and supplier replies.
- **Supabase/PostgreSQL** — structured runtime/state store already implemented, but currently connector-degraded: a 2026-08-19 retry of `select current_user, current_schema(), now()` still returned a permission error. Do not infer live schema while access is degraded.
- **Vercel** — deployment layer. A production project is READY, but the existing deployment must not be assumed to contain the latest GitHub Vertical 01 code until a new deployment is explicitly verified.
- **Claude** — independent auditor/second opinion through the shared handoff layer; not a second source of truth. Current PR #1 review remains pending.

## Vertical 01 maturity

Current main chain:

`Evidence -> Relationship -> Signal -> Opportunity -> Outcome`

Implemented in GitHub with stable IDs, provenance checks, entity consistency, outcome-state invariants, and real evidence-linked fixtures for SupplierTR, GH Petro, and YAXING.

Current maturity:

`Implemented in GitHub -> structural validation + GitHub Actions verified -> live Notion relationship/outcome proof exists -> Supabase adapter pending verified schema access -> not deployed as current Vercel runtime -> not production`

Draft PR #1 (`feature/evidence-classification`) is **not merged**. It adds explicit epistemic evidence classes (`fact | claim | estimate | inference | hypothesis | assumption | unknown`) so supplier statements cannot silently become verified facts. Latest corrected PR head previously passed GitHub Actions; Claude KEEP/CHANGE/STOP review remains pending.

## First measured loop proof

Notion contains evidence-backed Relationship Signals for SupplierTR, GH Petro and YAXING, each linked to canonical Entity Registry entries and Gmail evidence.

A YAXING micro-outcome is recorded in the canonical Outcome Ledger: technical engagement/catalog receipt progressed the route, but buyer-side engineering data (final Hydrotester pipe-length and wall-thickness/ID range) is now the explicit next blocker. The record is **Inconclusive / Retest**, not supplier qualification.

Older GH Petro, SupplierTR and K+S Outcome Ledger records were re-audited. Supplier capability/progression statements were rewritten to preserve claim semantics, and uncalibrated numeric scores were removed where they created pseudo-precision.

## Requirement Readiness Gate — shadow mode

Repeated field evidence from Marley and YAXING produced a Research Registry inference and Experiment Lab design: missing buyer-side decision-critical requirements may be an upstream bottleneck before final quotation/compliance comparison.

Draft PR #2 (`feature/requirement-readiness-shadow`) implements the smallest testable shadow-mode evaluator:

- `approved`
- `provisional`
- `unknown_blocking`
- separate `ready_for_discovery` and `ready_for_final_request`
- no external action or autonomous blocking

Self-audit correction: the first fixture treated communicated Hydrotester OD/pressure values as approved. This was too strong because Gmail proves communication, not current engineering authority. Latest PR #2 therefore keeps OD `89–180 mm` and max machine rating `120 MPa` as **provisional** until an approved source-of-authority record is linked; pipe length and wall-thickness/ID remain `unknown_blocking`. GitHub Actions run `32245181605` completed with conclusion `success` on latest PR #2 head `1c2694ec`.

The Experiment Lab remains **Designed / Pending** despite passing code tests. It needs 3–5 real equipment RFQs before any claim that the gate improves supplier clarification rounds or time-to-comparable-quote.

## Current hard gates

1. No new agent/registry/framework/integration merely to create activity.
2. No Supabase adapter based on remembered or guessed schema.
3. No supplier is commercially qualified merely because a structural test fixture validates.
4. No final Hydrotester length/wall-thickness assumption until engineering confirms it.
5. Communicated or historical buyer values are not engineering authority unless an approved source is linked.
6. No external consequential action without human approval.
7. No claim that current GitHub code is deployed on Vercel until deployment parity is verified.
8. No production AI-agent runtime before the procurement loop is measurable and repeatable.
9. Draft PRs must not be merged merely because CI passed; evidence correctness and review still matter.

## Drift rules

- Stable project context can be older than runtime. Runtime facts must be re-verified before action.
- A newer verified GitHub/Notion/Gmail/Supabase artifact supersedes older narrative state only for the fields it actually proves.
- Backup pages are lineage snapshots, not live operating objects.
- Code maturity must always be stated as Designed / Implemented / Tested / Deployed / Production separately.
- Unit-test fixture source refs may be synthetic only when the fixture is explicitly synthetic; real-case fixtures must never invent authority references.

## Verified research decisions — 2026-08-19

### GitHub Actions

The NEXUS test workflow has `workflow_dispatch`, `pull_request`, main-push execution and explicit least-privilege `contents: read`. CI is operational and has passed on multiple draft-PR heads, including PR #2 run `32245181605`.

### Supabase security/access

Connector access is still permission-blocked even for a minimal identity/schema query. Treat this as an integration/role-access problem before touching application RLS/schema. When access returns, inspect role, grants and RLS separately and use least privilege. Do not expose service-role/bypass credentials to a client.

### Hydrotester readiness research

Primary manufacturer material supports the readiness model, not buyer values: Fives Taylor-Wilson describes variation by pipe length, end conditions, pressure settings and sealing arrangements; YAXING describes non-standard customized hydrotesters designed from customer parameters such as pipe diameter, length and maximum pressure, with hold-time/station/sealing choices. Marley independently requested pipe-length and wall-thickness ranges before a detailed proposal. Therefore geometry and test parameters should be explicitly classified before final comparison, while buyer-approved values must come from the buyer/engineering authority.

### Future Signal Registry canonicalization

`NEXUS Future Signal Registry` at `5f728db4-2dfb-4ece-9c80-29707a118383` / `collection://ae665f6a-e726-4936-8e31-2b67e45b7ba9` remains the canonical write target. A unique source-less regional logistics Watch item from sibling `65efe565...` was re-researched against current IMO evidence, corrected at source, and merged into the canonical registry. The sibling remains lineage/recovery and should receive no new writes.

### Page duplicate canonicalization

Canonical Object Registry now explicitly records these live-under-Command-Center pages as Canonical Write, with matching siblings under the AGENT-FLEET backup Command Center preserved as read-only recovery/lineage:

- `NEXUS Parallel Execution Control — LIVE`
- `NEXUS Work Transfer Manifest — LIVE`
- `NEXUS Software Build Log — Qualification Engine v0.1`

No archive/delete/move was performed.

## Near-term proof targets

1. Receive Claude KEEP/CHANGE/STOP review of draft PR #1.
2. Keep PR #2 in shadow mode; collect 3–5 real RFQ observations before promotion or merge decision tied to workflow value.
3. Restore Supabase read access; inspect integration role/grants/RLS before changing policies or code.
4. Obtain Hydrotester pipe-length and wall-thickness/ID range from engineering and advance Marley / Yedi Mavi / ANZ without specification drift.
5. Record the next supplier reply/quote/referral as a measured outcome and compare expected vs actual Next Best Action.
6. Verify Vercel deployment parity only when a deliberate deployment is justified; do not deploy merely to show activity.
7. Only after repeated loop proof, begin Proposal Ingestion / deviation extraction v0.2.
8. Produce one final Work-migration parity checkpoint before changing orchestration surface.
