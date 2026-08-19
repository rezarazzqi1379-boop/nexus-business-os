# NEXUS Runtime Checkpoint — 2026-08-19

## Verified live systems

- GitHub repository: `rezarazzqi1379-boop/nexus-business-os` is accessible and writable.
- Git history contains coded Vertical 01, tests, stable-ID refactor, and pytest CI workflow.
- Gmail procurement evidence is live for SupplierTR, GH Petro, YAXING, Marley, ANZ, Yedi Mavi and KCl/BPC→OMS routes.
- Notion Command Center and Cross-AI Handoff Log are live.

## Vertical 01 status

Implemented:

`Gmail Evidence -> Relationship -> Signal -> Opportunity -> Outcome`

Current model rules include stable IDs, evidence linkage, entity consistency, and terminal-outcome consistency.

Real-case structural validation set:

1. SupplierTR — engineering evaluation started.
2. GH Petro — relevant OCTG/steel-pipe capability reply received.
3. Karat Machinery / YAXING — supplier engagement + machinery catalog received.

These are evidence-linked structural validation cases, not claims that any supplier has been commercially qualified or awarded.

## Current blockers / degraded integrations

- Supabase connector currently returns a permission error. Treat Supabase as degraded until direct read access is verified again. Do not invent schema mappings while blocked.
- Notion `query_data_sources` usage limit is currently reached; search/fetch remain available. Avoid plan upgrade unless query volume becomes a real operating bottleneck.
- GitHub Actions workflow exists, but a successful CI run has not yet been verified from the available connector evidence.

## Canonical operating architecture

- ChatGPT: Control Plane / executor for tasks supported by available tools.
- Claude: independent auditor / second opinion; direct executor only when explicitly useful.
- GitHub: source of truth for code and version history.
- Supabase: intended structured runtime/state store once access is healthy.
- Notion: human-readable coordination, canonical object map, cross-AI handoff.
- Gmail: live business communication evidence.

## Do-not-expand gate

Do not add a new agent, registry, framework or integration merely to show progress. Before expansion, prove repeatable value on the three real procurement cases and resolve canonical state / duplicate debt.

## Next execution priorities

1. Verify pytest CI actually runs and passes.
2. Review Claude findings on Vertical 01 v0.2 and duplicate LIVE pages.
3. Resolve Supabase permission and map the coded model to the real schema only after verification.
4. Convert incoming supplier replies into evidence-backed pipeline updates.
5. When engineering clarifications arrive, update Marley/Yedi Mavi/ANZ communications without mixing Heat-Treatment dimensions into Hydrotester requirements.
6. Preserve a migration checkpoint before moving the active project into Work.
