# NEXUS Cross-Project Integration Contract v0.1

Status: implemented in Supabase runtime on 2026-08-22.

## Purpose

NEXUS projects must not operate as isolated chat, Notion, code, CRM, sourcing, or research silos. All project-specific work resolves through one shared organizational graph while preserving project scope and source lineage.

## Canonical Runtime Roles

- Supabase/PostgreSQL: canonical cross-project data substrate.
- Notion Command Center: human-facing operational workspace and resume/checkpoint surface.
- GitHub: version-controlled code, tests, architecture, policies, and migration documentation.
- Vercel: production command-center deployment surface.
- Chat/Gmail/files/web: evidence and interaction sources, not canonical truth stores.

## Shared Graph Objects

Every project may link to canonical entities, aliases, claims, evidence, relationships, interactions, signals, need hypotheses, opportunities, proposals, outcomes, ideas, experiments, and lessons.

Project-specific records must retain lineage. Cross-project reuse is allowed only with lineage and deduplication.

## Project Registry

Canonical tables:

- `nexus_projects`
- `nexus_project_links`

Known project families include industrial machinery sourcing, KCl import, coffee and food-additives import, mining/investment analysis, growth/content systems, portfolio/software projects, commercial documents, and NEXUS itself.

Lifecycle state `known` means discovered/registered, not automatically active or approved for outreach.

## Agent Contract

Each production agent must have explicit `data_scope` and `memory_policy`.

Minimum rules:

1. Resolve entities before creating duplicates.
2. Separate facts, claims, estimates, inferences, hypotheses, assumptions, and unknowns.
3. Preserve provenance for every durable knowledge write.
4. Scope work to a project when project context exists.
5. Reuse cross-project knowledge only with lineage.
6. External outreach, financial commitments, and destructive actions remain gated.
7. Outcomes may generate bounded lessons; lessons do not silently mutate production policy.

## Component Dependencies

Canonical dependency map: `nexus_component_dependencies`.

Key dependencies:

- Orchestrator -> Organizational Intelligence Graph
- Evidence Verifier -> Claims/Evidence graph
- Future Signal Scout -> Entity/Signal graph
- Opportunity Matcher -> Opportunity Discovery Engine
- Supplier & Connector Scout -> Relationship Capital Graph
- Relationship Strategist -> Relationship Capital Graph
- Outcome Learning -> Controlled Learning Engine
- Memory Curator -> Project Registry
- Notion Command Center -> Project Registry (workspace sync)
- Vercel Command Center -> Project Registry (UI)
- Proposal Qualifier -> canonical requirements/claims/evidence

## Closed Loop

`Source -> Entity Resolution -> Claim -> Evidence -> Relationship -> Need Hypothesis -> Opportunity -> Next Best Action -> Outcome -> Lesson`

The KPI is not agent count. Primary operational measures are verified entity yield, relationship-path quality, qualified opportunity precision, duplicate-outreach avoidance, response/quote/order progression, and lesson validity.

## Current Verified Infrastructure

- Supabase project: active and healthy.
- Notion Command Center: reachable and recently updated.
- GitHub repository: reachable with write/admin access.
- Vercel project: production deployment in READY state.

## Drift Rule

Runtime evidence overrides stale documentation. When a component changes, update `nexus_runtime_state`, this contract when semantics change, and any affected tests/checkpoints.