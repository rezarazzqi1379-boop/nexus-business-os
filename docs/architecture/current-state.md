# NEXUS Current-State Architecture

Verified: 2026-08-19

This file is the code-repository current-state manifest. It does not replace the stable NEXUS Master Context; it records runtime changes that supersede older roadmap wording about what is already live.

## Source-of-truth split

- **ChatGPT / NEXUS HQ** — control plane, orchestration, analysis, execution when a connected tool supports the action. Not the sole memory store.
- **GitHub** — canonical source of truth for NEXUS code, tests, CI configuration, and version history.
- **Notion** — human-readable operational coordination, canonical-object map, decisions, and Cross-AI Handoff Log.
- **Gmail** — primary evidence for live commercial communications and supplier replies.
- **Supabase/PostgreSQL** — structured runtime/state store already implemented, but currently connector-degraded because even a minimal `select now()` returns a permission error. Do not infer live schema while access is degraded.
- **Vercel** — deployment layer. A production project is READY, but the existing deployment must not be assumed to contain the latest GitHub Vertical 01 code until a new deployment is explicitly verified.
- **Claude** — independent auditor/second opinion and occasional direct executor through the shared handoff layer; not a second source of truth.

## Vertical 01 maturity

Current chain:

`Evidence -> Relationship -> Signal -> Opportunity -> Outcome`

Implemented in GitHub with stable IDs, provenance checks, entity consistency, outcome-state invariants, and real evidence-linked fixtures for SupplierTR, GH Petro, and YAXING.

Maturity label:

`Implemented in GitHub -> local logic/tests exercised -> GitHub Actions configured -> successful CI run not yet independently verified -> Supabase adapter pending verified schema access -> not production`

Local re-validation on 2026-08-19 confirmed all three real structural fixtures return zero invariant errors. This is not a substitute for repository CI.

## Current hard gates

1. No new agent/registry/framework/integration merely to create activity.
2. No Supabase adapter based on remembered or guessed schema.
3. No supplier is commercially qualified merely because a structural test fixture validates.
4. No final Hydrotester length/wall-thickness assumption until engineering confirms it.
5. No external consequential action without human approval.
6. No claim that current GitHub code is deployed on Vercel until deployment parity is verified.
7. No production AI-agent runtime before the first procurement loop is measurable and repeatable.

## Drift rules

- Stable project context can be older than runtime. Runtime facts must be re-verified before action.
- A newer verified GitHub/Notion/Gmail/Supabase artifact supersedes older narrative state only for the fields it actually proves.
- Backup pages are lineage snapshots, not live operating objects.
- Code maturity must always be stated as Designed / Implemented / Tested / Deployed / Production separately.

## Verified research decisions — 2026-08-19

### GitHub Actions

Official GitHub documentation confirms workflow runs emit Checks and can be inspected from run history/logs. The NEXUS test workflow now has `workflow_dispatch` plus explicit least-privilege `contents: read`. A successful run is still UNKNOWN because the available connector exposes no workflow-run/check result for current main.

### Supabase security/access

Official Supabase documentation separates object grants from Row Level Security: grants determine whether a role can reach an object; RLS determines which rows it can access. Because the connector currently fails even on `select now()`, treat this first as an integration/role-permission failure rather than automatically rewriting table RLS policies. When access returns, inspect role/grants/RLS separately and use least privilege. Service-role or bypass-RLS credentials must never be exposed to a client.

### Future agent/runtime direction

Current OpenAI Agents SDK guidance favors a small set of primitives: agents, tools/handoffs, guardrails, human-in-the-loop, sessions, and tracing. NEXUS should not create a large agent fleet. If/when agentic runtime is justified, start with one manager/orchestrator plus specialist tools or handoffs and make tracing/evaluation mandatory. Sensitive model/tool payload capture should default off for commercial data. OpenTelemetry GenAI conventions are still evolving, so keep internal trace/event contracts portable rather than binding the database schema to experimental telemetry names.

### Hydrotester feasibility research

Official manufacturer pages show that the 120 MPa class is technically credible: Fives Taylor-Wilson describes stable testing from 35 bar to over 1,750 bar and accommodates varying pipe lengths/end conditions; YAXING publishes customized hydrotesters up to 150 MPa and pipe lengths up to 25 m. These sources support feasibility of the pressure class, not compliance of any specific offered machine. Marley has independently asked for pipe length and wall-thickness ranges before quotation, reinforcing that geometry remains a decision-critical engineering input.

## Near-term proof targets

1. Verify CI success on current main; if the connector remains blind, manually inspect Actions when Work/Codex access is available.
2. Receive Claude KEEP/CHANGE/STOP review of Vertical 01 v0.2.
3. Restore Supabase read access; inspect integration role/grants/RLS before changing policies or code.
4. Turn the three structural fixtures into synchronized runtime records once DB access is verified.
5. Obtain Hydrotester pipe-length and wall-thickness range from engineering and advance Marley / Yedi Mavi / ANZ without specification drift.
6. Convert at least one supplier interaction into a measured closed loop with outcome/next-action evidence before Proposal Ingestion v0.2 expands.
7. Produce a final Work-migration parity checkpoint before changing orchestration surface.
