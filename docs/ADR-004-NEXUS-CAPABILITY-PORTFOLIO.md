# ADR-004: NEXUS Capability Portfolio and rollout waves

## Status

Proposed; branch-only until reviewed and merged.

## Decision

Expand the audited tool portfolio from six to twelve candidates while keeping
every candidate disabled by default and read-only at first contact. The
registry now covers GitHub, Gmail, Google Drive, Notion, HubSpot, Apollo,
filesystem, Playwright, Zotero, Canva, Figma and Supabase.

Each candidate declares its project scope, cost class, harmless health probe,
fallback and exact-approval rule for writes. This separates tool discovery from
connection, connection from activation, and activation from production proof.

## Rollout

- NOW: existing-source and local evidence probes (GitHub, Gmail, Drive, filesystem)
- NEXT: bounded project pilots (Notion, HubSpot, Playwright, Zotero)
- LATER/METERED: design/data/paid pilots (Canva, Figma, Supabase, Apollo)

Only one new connector should enter a live pilot at a time. A pilot must prove
identity, minimum permissions, project isolation, useful output, auditability,
failure behavior and rollback before promotion.

## Non-goals

- automatic installation or OAuth connection
- broad write scopes
- replacing an existing working capability without comparative evidence
- treating the number of tools as a success metric

## Rollback

Remove or disable the candidate manifest. Existing native/manual workflows
remain the declared fallback and no database migration is introduced.
