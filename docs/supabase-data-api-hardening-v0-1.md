# Supabase Data API Hardening v0.2

Status: **LIVE POSTURE REVERIFIED / HARDENING NOT APPLIED**

Verified: 2026-08-23
Project: `jhmhtrzhcpdfkoflnsac`

This document is a Forge re-verification of the NEXUS Supabase posture. It records current read-only evidence and a reversible hardening plan. It does not authorize or apply any production access change.

## Current verified state

- Supabase project status: `ACTIVE_HEALTHY`.
- Live SQL access succeeds as `postgres` in schema `public`.
- Current inventory contains 30 base tables matching `public.nexus_*`; information-schema inventory also exposes 33 `nexus_*` relations when non-base-table relations are included.
- `nexus_projects`: 13 rows.
- `nexus_runtime_state`: 21 rows.
- `nexus_lessons`: 2 rows.
- `nexus_promotion_gates`: 3 rows.
- `nexus_outcomes`: 1 row.
- Public PostgreSQL function count at re-verification: 0.

The earlier repository wording that Supabase connector access was permission-blocked is stale for the current session. PR #31's basic claim that a Supabase runtime exists is now supported by live evidence, but individual runtime-state/content claims must still be checked field-by-field before use.

## RLS / grant posture

Security Advisor currently reports `rls_enabled_no_policy` on many `public.nexus_*` tables. The direct catalog replay confirms the base tables have RLS enabled and zero policies.

This does **not** by itself prove data exposure. With RLS enabled and no policies, ordinary API row access is fail-closed. However, the grant surface is broader than necessary for an internal-only data model:

- `service_role` currently has table privileges across all 33 discovered `nexus_*` relations in the role-grant inventory.
- `anon` and `authenticated` currently hold broad relation privileges on 16 discovered relations in the role-grant inventory.
- For the 30 base tables inspected directly, 13 currently show `anon` and `authenticated` grants while RLS remains enabled with zero policies.

This combination is currently fail-closed at the row-policy layer, but it creates unnecessary future risk: adding a weak RLS policy later could unexpectedly expose a relation that already has API-role grants.

## Forge diagnosis

Observed mechanism:
`public schema + Data API roles + table grants + RLS`

Current protection:
`RLS enabled + no policies -> row access denied`

Current weakness:
`broad grants remain latent authority and increase the blast radius of a future policy mistake`

Do not “fix” the Advisor by inventing permissive policies. NEXUS still lacks a proven shared ownership/tenancy model suitable for honest `auth.uid()` row authorization across all internal tables.

## Recommended end state

### Preferred — internal data plane not exposed to browser/API roles

If final dependency verification confirms no required REST/GraphQL client path, keep NEXUS operational tables as backend/internal state and remove unnecessary `anon`/`authenticated` grants. If product configuration allows a clean separation, disabling or narrowing the Data API exposure for the internal schema is simpler than maintaining fake user policies.

### If a user-facing data plane is required later

Design explicit tenancy/ownership first (`workspace_id`, `tenant_id`, membership/role model). Then expose only a small allowlisted API surface through dedicated tables/views/RPCs with reviewed RLS. Do not retrofit one generic policy across all NEXUS tables.

## Required pre-mutation gates

Before any `REVOKE`, Data API configuration change, schema move, or RLS-policy write:
1. verify current frontend/backend dependencies;
2. capture exact ACL/default-privilege snapshot;
3. confirm which relations, if any, require `anon` or `authenticated` access;
4. smoke-test Edge Functions and deployed application paths;
5. define rollback as minimum per-relation re-grants, not blanket restoration;
6. require exact human approval for the production mutation.

## Acceptance matrix after any approved hardening

1. Inventory parity is preserved.
2. Internal NEXUS tables have no unintended `anon` CRUD.
3. `authenticated` access is only explicit/allowlisted.
4. Future default privileges do not silently widen API-role access.
5. Edge Functions and backend paths still work.
6. Deployed UI has no legitimate Data API regression.
7. API/Postgres logs show no new legitimate permission failures.
8. Security Advisor is rerun and findings are interpreted in context rather than “fixed” by permissive policies.
9. No service-role key appears in public/client code.
10. Rollback proof exists for the exact changed permissions.

## Current decision

**HOLD production mutation.** The hardening hypothesis remains plausible and stronger than the old broad-grant posture, but the next action is dependency verification plus exact ACL/default-privilege capture. No production SQL was changed in this Forge pass.

## Non-goals

- no invented RLS policy;
- no automatic Data API disable;
- no production revoke from this document;
- no service-role exposure;
- no claim that an Advisor lint alone proves data leakage;
- no claim that project health equals application correctness.