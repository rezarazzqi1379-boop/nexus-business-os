# NEXUS Current-State Architecture

Verified: 2026-08-19

This file is the code-repository current-state manifest. It does not replace the stable NEXUS Master Context; it records runtime changes that supersede older roadmap wording about what is already live.

## Source-of-truth split

- **ChatGPT / NEXUS HQ** — control plane, orchestration, analysis, execution when a connected tool supports the action. Not the sole memory store.
- **GitHub** — canonical source of truth for NEXUS code, tests, CI configuration, and version history.
- **Notion** — human-readable operational coordination, canonical-object map, decisions, and Cross-AI Handoff Log.
- **Gmail** — primary evidence for live commercial communications and supplier replies.
- **Supabase/PostgreSQL** — structured runtime/state store already implemented, but currently connector-degraded because read queries return a permission error. Do not infer live schema while access is degraded.
- **Vercel** — deployment layer. A production project is READY, but the existing deployment must not be assumed to contain the latest GitHub Vertical 01 code until a new deployment is explicitly verified.
- **Claude** — independent auditor/second opinion and occasional direct executor through the shared handoff layer; not a second source of truth.

## Vertical 01 maturity

Current chain:

`Evidence -> Relationship -> Signal -> Opportunity -> Outcome`

Implemented in GitHub with stable IDs, provenance checks, entity consistency, outcome-state invariants, and real evidence-linked fixtures for SupplierTR, GH Petro, and YAXING.

Maturity label:

`Implemented in GitHub -> local logic/tests exercised -> GitHub Actions configured -> successful CI run not yet independently verified -> Supabase adapter pending verified schema access -> not production`

## Current hard gates

1. No new agent/registry/framework/integration merely to create activity.
2. No Supabase adapter based on remembered or guessed schema.
3. No supplier is commercially qualified merely because a structural test fixture validates.
4. No final Hydrotester length/wall-thickness assumption until engineering confirms it.
5. No external consequential action without human approval.
6. No claim that current GitHub code is deployed on Vercel until deployment parity is verified.

## Drift rules

- Stable project context can be older than runtime. Runtime facts must be re-verified before action.
- A newer verified GitHub/Notion/Gmail/Supabase artifact supersedes older narrative state only for the fields it actually proves.
- Backup pages are lineage snapshots, not live operating objects.
- Code maturity must always be stated as Designed / Implemented / Tested / Deployed / Production separately.

## Near-term proof targets

1. Verify CI success on current main.
2. Receive Claude KEEP/CHANGE/STOP review of Vertical 01 v0.2.
3. Restore Supabase read access and map the code to the real schema.
4. Turn the three structural fixtures into synchronized runtime records once DB access is verified.
5. Process engineering clarification and advance Marley / Yedi Mavi / ANZ without specification drift.
6. Produce a final Work-migration parity checkpoint before changing orchestration surface.
