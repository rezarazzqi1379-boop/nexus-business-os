# NEXUS Current-State Architecture

Verified: 2026-08-19

This file is the code-repository current-state manifest. It does not replace the stable NEXUS Master Context; it records runtime changes that supersede older roadmap wording about what is already live.

## Source-of-truth split

- **ChatGPT / NEXUS HQ** — control plane, orchestration, analysis, execution when a connected tool supports the action. Not the sole memory store.
- **GitHub** — canonical source of truth for NEXUS code, tests, CI configuration, and version history.
- **Notion** — operational coordination, canonical-object map, decisions, relationship signals, outcome learning, research/experiments, and Cross-AI Handoff Log.
- **Gmail** — primary evidence for live commercial communications and supplier replies/drafts.
- **Supabase/PostgreSQL** — structured runtime/state store already implemented, but connector access remains degraded; a current `select current_user, current_schema(), now()` still returns a permission error. Do not infer schema or rewrite RLS while blocked.
- **Vercel** — deployment layer. Production is READY, but direct fetch verifies the current deployment serves only `NEXUS Business OS — Runtime bootstrap checkpoint`; current Python Vertical 01 / draft-PR code is not deployed there.
- **Claude** — independent auditor through the shared handoff layer; not a second source of truth. PR #1 review remains Open with no response/comments.

## Vertical 01 maturity

Current main chain:

`Evidence -> Relationship -> Signal -> Opportunity -> Outcome`

Main contains stable IDs, provenance checks, entity consistency, outcome-state invariants, real Gmail-linked cases, verified GitHub Actions, and live Notion relationship/outcome proof. It is not yet synchronized to the verified Supabase runtime and is not production.

Draft PR #1 (`feature/evidence-classification`, head `9596b15e`) adds explicit epistemic classes:

`fact | claim | estimate | inference | hypothesis | assumption | unknown`

It also preserves claim semantics downstream so supplier statements are not silently promoted to facts. Corrected head passed GitHub Actions run `32244193115`. PR remains draft/unmerged pending independent review.

## Requirement Readiness Gate — shadow mode

Repeated field evidence from Marley and YAXING produced a Research Registry inference and a Designed/Pending Experiment Lab test.

Draft PR #2 (`feature/requirement-readiness-shadow`, head `1dbe2546`) implements:

- `approved`
- `provisional`
- `unknown_blocking`
- separate `ready_for_discovery` and `ready_for_final_request`
- retrievable source refs for approved/provisional values
- no external action or autonomous blocking
- source-separated Hydrotester Requirement Input Map

Current Hydrotester shadow state:

- OD `89–180 mm` — **provisional** until engineering authority is linked
- max machine rating target `120 MPa` — **provisional** until engineering authority is linked
- final pipe-length range — **unknown_blocking**
- final wall-thickness / ID range — **unknown_blocking**
- historical communicated `12 m` — provisional, not authority

Latest PR #2 GitHub Actions run `32245386558` completed successfully. Passing tests prove implementation integrity, not field value. The gate must be observed across 3–5 real comparable equipment RFQs before promotion or workflow-value claims.

## Live procurement evidence and qualification state

### OCTG / Hydrotester / Heat Treatment

Canonical Entity Registry and Relationship Signals now include Marley, ANZ Global and Yedi Mavi in addition to SupplierTR, GH Petro and YAXING.

- **Marley** — responsive and asked for Hydrotester pipe-length and wall-thickness ranges before detailed quotation. Official-site review verifies Wuxi Marley Technology identity and the Eli contact, but the public portfolio currently emphasizes evaporation, heat-exchange and process equipment; no pipe/OCTG hydrotester product was found in focused review. Correct status: role/capability **unverified**, not rejected. Ask direct-manufacturer vs integrator vs third-party OEM identity and references.
- **ANZ Global** — responsive UAE sourcing/integration route. Keep ANZ capability separate from OEM technical capability. Require named manufacturer, location, scope/exclusions, deviations, commercial terms, fee/markup and executable Iran route.
- **Yedi Mavi** — responsive Turkish sourcing route, RFQ `YM-2026-0819-OCTG`. Require structured OEM shortlist, references, deviations, fee transparency and executable Iran route.
- **SupplierTR** — supplier reports engineering evaluation active; OEM shortlist and compliance remain unverified.
- **GH Petro** — substantive reply and capability claim; technical qualification remains open.
- **YAXING** — catalog/technical engagement is fact; final Hydrotester geometry remains unresolved.

Gmail drafts for Marley, ANZ and Yedi Mavi were updated to preserve provisional/unknown semantics, keep Heat Treatment dimensions separate from Hydrotester requirements, and ask for actual OEM/manufacturing scope. They remain drafts and were not sent.

### KCl / Belaruskali / OMS

BPC factually referred ASAK to Overseas Material Supply (OMS) for Iranian-market distribution. OMS then provided concrete commercial terms:

- CFR basis
- AED payment
- 50% advance upon booking
- balance against copies of shipping documents
- usual shipment lot around 3,000 MT
- possible combined shipment for ASAK's approximately 1,200 MT requirement

OMS also states it is an exclusive Belaruskali agent, has supplied Iran for a long time, and that a specific Ministry of Agriculture permit is required. Those statements are not all independently verified for this transaction.

The previous Outcome Ledger label `qualified with compliance conditions` was corrected to **commercial route — compliance/import facts pending**, with `Inconclusive / Retest` semantics and uncalibrated numeric scores removed. A canonical OMS Relationship Signal was added.

Current research status for the permit issue: current web verification did not surface an authoritative Iranian government source establishing OMS's exact blanket permit requirement for industrial KCl feedstock used in SOP production. KCl has both agricultural and industrial uses, so exact HS/use classification and permit applicability remain **Unknown / Needs Check**. Verify via ASAK customs/import-registration expertise or authoritative trade-registration evidence before representing the route as compliant.

A reply draft to OMS was created, not sent. It states import history and permit status are under internal verification, asks OMS for the exact HS code and regulatory reference required for industrial SOP-feedstock KCl, and requests COA/TDS, packaging, CFR destination/price basis, lead time and SGS/inspection options.

K+S remains a direct compliance-rejected route for current Iran-related procurement unless new official evidence changes that status.

### Can machinery

The correct Golden Eagle contact thread uses `xugan@zjjyspjx.com`. The old draft addressed to `xugan@zijyspjx.com` is stale and must not be sent. Latest correct-thread outbound requested two commercial scopes: standalone Necking and combined Necking + Flanging + Beading + Seaming. No new supplier reply has been observed since that message; do not duplicate outreach without timing/evidence justification.

## First measured-loop proof

Notion contains evidence-backed Relationship Signals for SupplierTR, GH Petro, YAXING, Marley, ANZ, Yedi Mavi and OMS, each tied to retrievable evidence and canonical entities where resolved.

Outcome Ledger records for YAXING, GH Petro, SupplierTR, K+S and OMS were re-audited so claims, facts, unknowns and uncalibrated scores do not masquerade as qualification.

This is the current proof direction:

`Evidence -> Resolved Entity -> Relationship Signal -> Next Action -> Outcome -> Learning`

The remaining goal is repeated closed-loop performance, not more infrastructure.

## Current hard gates

1. No new agent/registry/framework/integration merely to create activity.
2. No Supabase adapter based on remembered or guessed schema.
3. No supplier is qualified merely because a fixture validates or a supplier is responsive.
4. No final Hydrotester length/wall-thickness assumption until engineering confirms it.
5. Communicated/historical buyer values are not engineering authority without an approved source.
6. Keep Heat Treatment dimensions separate from Hydrotester requirements.
7. No external consequential action without human approval.
8. No claim that current code is deployed on Vercel; bootstrap-only parity has been directly verified.
9. Draft PRs must not be merged merely because CI passed.
10. No production AI-agent runtime before procurement loops are measurable and repeatable.
11. Do not present uncalibrated heuristic scores as probabilities or precise confidence.

## Drift rules

- Runtime facts must be reverified before action.
- Newer verified artifacts supersede older narratives only for fields they actually prove.
- Backup pages are lineage snapshots, not live operating objects.
- Designed / Implemented / Tested / Deployed / Production are separate maturity states.
- Unit-test fixture authority refs may be synthetic only when explicitly synthetic; real-case fixtures must never invent authority.
- A supplier statement is evidence that the supplier made the statement; it is not automatically evidence that the underlying capability/compliance fact is true.

## Near-term proof targets

1. Receive Claude KEEP/CHANGE/STOP review of PR #1; no response exists yet.
2. Keep PR #2 in shadow mode and collect 3–5 real RFQ observations.
3. Restore Supabase read access; inspect role/grants/RLS/schema before adapter work.
4. Obtain engineering-approved Hydrotester length and wall-thickness/ID values plus hold-time/cycle and other decision-critical fields as needed.
5. Resolve Marley exact manufacturing/OEM role before qualification.
6. Resolve OMS industrial KCl HS/use/permit applicability and ASAK import-history/payment feasibility before commercial qualification.
7. Record next supplier reply/quote/referral against expected Next Best Action and outcome.
8. Begin Proposal Ingestion / deviation extraction only after repeated loop proof.
9. Keep Vercel undeployed until there is a deliberate runtime artifact worth deploying.
10. Produce one final Work-migration parity checkpoint only when the orchestration surface actually changes.
