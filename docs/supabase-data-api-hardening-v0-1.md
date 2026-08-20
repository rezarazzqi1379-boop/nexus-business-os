# Supabase Data API Hardening v0.1

Status: **PROPOSAL / NOT APPLIED**

This document records the verified 2026-08-20 NEXUS Supabase access posture and a reversible hardening plan. It does not authorize or apply any production access change.

## Verified current state

Project: `jhmhtrzhcpdfkoflnsac` (`ACTIVE_HEALTHY`).

Seventeen `public.nexus_*` tables are owned by `postgres`, have RLS enabled, and currently have zero RLS policies. Current PostgreSQL grants give `anon` and `authenticated` direct table privileges including SELECT/INSERT/UPDATE/DELETE. With RLS enabled and no policies, ordinary Data API row access fails closed, but the broad grants increase future risk if a weak policy is later added.

The current NEXUS schema does not provide a shared `user_id`, `tenant_id`, or `workspace_id` ownership column across these tables. Therefore user-scoped policies based on `auth.uid()` cannot be honestly introduced without a separate ownership/tenancy design.

The active Edge Function `nexus-proposal-qualifier` has `verify_jwt=true` and does not read or write database tables. A live audit found no PostgreSQL functions in the `public` schema. Repository searches found no current Supabase JS/SSR client, `NEXT_PUBLIC_SUPABASE_*`, `/rest/v1`, `/graphql/v1`, or `supabase.co` application dependency. The Supabase API log was empty for the previous 24 hours at the time of verification. This is strong evidence of no current Data API dependency, but not proof that no historical or external consumer has ever existed.

Default privileges in `public` currently auto-grant table/function/sequence privileges to API roles for objects created by `postgres` and `supabase_admin`. Therefore hardening only today's 17 tables is not future-safe.

## Recommended end state

### Preferred option — disable Data API if dependency remains zero

If a final dependency check confirms no required REST/GraphQL client path, disable the Supabase Data API at the project integration level. Keep Edge Functions separately authenticated. This creates the simplest boundary: internal tables remain database/backend state rather than an accidental public API surface.

Disabling the Data API is a production access change and requires an explicit human gate plus an immediate smoke test of all known live application paths.

### Defense-in-depth option — least-privilege grants

If Data API must remain enabled, remove direct `anon` and `authenticated` access from internal NEXUS tables and future defaults. Re-grant only explicitly required relations later.

Proposed SQL, **not yet applied**:

```sql
begin;

revoke all on table public.nexus_action_risk_taxonomy from anon, authenticated;
revoke all on table public.nexus_agent_runs from anon, authenticated;
revoke all on table public.nexus_agents from anon, authenticated;
revoke all on table public.nexus_entities from anon, authenticated;
revoke all on table public.nexus_evidence from anon, authenticated;
revoke all on table public.nexus_experiments from anon, authenticated;
revoke all on table public.nexus_identity_candidates from anon, authenticated;
revoke all on table public.nexus_identity_tests from anon, authenticated;
revoke all on table public.nexus_need_hypotheses from anon, authenticated;
revoke all on table public.nexus_opportunities from anon, authenticated;
revoke all on table public.nexus_outcomes from anon, authenticated;
revoke all on table public.nexus_proposal_claims from anon, authenticated;
revoke all on table public.nexus_proposals from anon, authenticated;
revoke all on table public.nexus_relationships from anon, authenticated;
revoke all on table public.nexus_requirements from anon, authenticated;
revoke all on table public.nexus_runtime_state from anon, authenticated;
revoke all on table public.nexus_signals from anon, authenticated;

alter default privileges for role postgres in schema public
  revoke select, insert, update, delete on tables from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke execute on functions from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke usage, select on sequences from anon, authenticated;

commit;
```

`service_role` is deliberately not revoked in this proposal because future trusted server-side/database workflows may require it. Any service-role use must remain server-only and must never be exposed in frontend code.

## Rollback concept

Rollback must restore only privileges that are proven necessary, not blindly reinstate blanket access. If an application dependency is discovered after a revoke, identify the exact relation and operation and grant only that minimum permission, for example:

```sql
grant select on public.some_explicit_api_table to authenticated;
```

Do not restore blanket CRUD to all NEXUS tables merely to make an unknown client work.

If the Data API itself was disabled and a validated dependency requires it, re-enable the integration first, then apply explicit per-object grants plus reviewed RLS policies.

## Acceptance test matrix

1. **Inventory parity** — read-only audit lists exactly the intended `public.nexus_*` relations and their RLS/policy/grant state.
2. **Anon denial** — `anon` has no direct SELECT/INSERT/UPDATE/DELETE privilege on internal NEXUS tables after hardening.
3. **Authenticated denial** — `authenticated` has no direct CRUD privilege unless explicitly allowlisted.
4. **Future-safe defaults** — newly created internal tables/functions/sequences do not automatically gain API-role privileges.
5. **Edge Function continuity** — `nexus-proposal-qualifier` still accepts a valid JWT and produces the same pure-compute response.
6. **Frontend smoke test** — current deployed web application routes still load without Supabase Data API errors.
7. **API log check** — no unexpected 401/403/42501 spike from a legitimate dependency after hardening.
8. **Security Advisor** — rerun security advisor and classify remaining RLS-no-policy findings in context; internal ungranted tables may intentionally have no user policy.
9. **No privilege widening** — no remediation may introduce service-role secrets into browser/client code.
10. **Rollback readiness** — exact previous ACL snapshot is captured before any production mutation.

## Longer-term architecture

If NEXUS develops a real user-facing Supabase data plane, first design explicit ownership/tenancy (`workspace_id`/`tenant_id`/user membership), then expose a small dedicated API schema or allowlisted views/RPCs. Internal operational tables should move toward a non-exposed schema rather than treating `public` as the permanent internal storage boundary.

## Non-goals

- no invented RLS policies without a real ownership model;
- no production migration from this document alone;
- no Data API enable/disable without explicit human approval;
- no frontend service-role key;
- no claim that RLS lint alone proves data leakage.
