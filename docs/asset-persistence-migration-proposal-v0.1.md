# Asset Persistence Migration Proposal v0.1

Status: Proposal only. Do not apply to production without Human Gate, backup, RLS/security review, and migration test.

## Goal
Persist multimodal AssetRecords and semantic-search metadata without creating a parallel database architecture.

## Existing fit
Reuse existing `nexus_entities`, `nexus_evidence`, `nexus_relationships`, and `nexus_runtime_state` where appropriate. Add a dedicated asset table only because file/version/copy-state semantics are materially different from generic entities.

## Proposed tables

```sql
create table if not exists public.nexus_assets (
  id uuid primary key default gen_random_uuid(),
  asset_key text not null unique,
  file_name text not null,
  source text not null,
  kind text not null,
  stable_ref text not null,
  source_version_ref text not null,
  observed_at timestamptz not null,
  project_refs text[] not null default '{}',
  goal_refs text[] not null default '{}',
  evidence_refs text[] not null default '{}',
  sensitivity text not null,
  analysis_state text not null,
  content_sha256 text,
  copy_state text not null default 'reference_only',
  physical_backend text,
  physical_ref text,
  expected_sha256 text,
  restored_sha256 text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(stable_ref, source_version_ref)
);
```

Optional semantic indexing (requires pgvector extension and explicit migration approval):

```sql
create extension if not exists vector;
alter table public.nexus_assets add column if not exists embedding vector(1536);
create index if not exists nexus_assets_embedding_hnsw
  on public.nexus_assets using hnsw (embedding vector_cosine_ops);
```

Embedding dimension must be bound to the actual embedding model used at deployment time; `1536` above is a placeholder and must not be treated as production truth.

## Invariants
- same asset_key cannot silently point to another source_version_ref
- changed source version invalidates previous analysis/embedding unless explicitly versioned
- credential_secret assets must never be persisted as ordinary long-term asset rows
- reference_only is not physical backup proof
- copied_verified requires exact expected/restored digest match and backend/storage reference
- semantic index failure must not block deterministic ref/project/goal retrieval
- historical/superseded asset versions remain queryable for provenance

## Migration sequence
1. Full checkpoint and export of current schema metadata
2. Security/RLS review
3. Apply migration to a non-production branch/project first
4. Run persistence, idempotency, duplicate, stale-analysis, and restore-proof tests
5. Verify query plans/index behavior
6. Human Gate
7. Apply production migration
8. Read-back and rollback-plan verification

No migration has been applied by this proposal.