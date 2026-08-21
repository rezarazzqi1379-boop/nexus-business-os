-- NEXUS least-privilege hardening migration
-- STATUS: REVIEWED ARTIFACT ONLY / NOT YET APPLIED
-- This file intentionally does not create user-scoped RLS policies because the current
-- schema has no shared ownership/tenant key. It only removes direct API-role grants.
-- Human Gate required before production execution.

begin;

-- Fail closed if the reviewed inventory changed. Re-audit before editing this number.
do $$
declare
  nexus_table_count integer;
  unexpected_policy_count integer;
begin
  select count(*) into nexus_table_count
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname like 'nexus_%';

  if nexus_table_count <> 17 then
    raise exception 'NEXUS table inventory drifted: expected 17, found %; rerun audit first', nexus_table_count;
  end if;

  select count(*) into unexpected_policy_count
  from pg_policy p
  join pg_class c on c.oid = p.polrelid
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relname like 'nexus_%';

  if unexpected_policy_count <> 0 then
    raise exception 'NEXUS RLS policy state changed: expected 0 policies, found %; review before hardening', unexpected_policy_count;
  end if;
end $$;

revoke all privileges on table public.nexus_action_risk_taxonomy from anon, authenticated;
revoke all privileges on table public.nexus_agent_runs from anon, authenticated;
revoke all privileges on table public.nexus_agents from anon, authenticated;
revoke all privileges on table public.nexus_entities from anon, authenticated;
revoke all privileges on table public.nexus_evidence from anon, authenticated;
revoke all privileges on table public.nexus_experiments from anon, authenticated;
revoke all privileges on table public.nexus_identity_candidates from anon, authenticated;
revoke all privileges on table public.nexus_identity_tests from anon, authenticated;
revoke all privileges on table public.nexus_need_hypotheses from anon, authenticated;
revoke all privileges on table public.nexus_opportunities from anon, authenticated;
revoke all privileges on table public.nexus_outcomes from anon, authenticated;
revoke all privileges on table public.nexus_proposal_claims from anon, authenticated;
revoke all privileges on table public.nexus_proposals from anon, authenticated;
revoke all privileges on table public.nexus_relationships from anon, authenticated;
revoke all privileges on table public.nexus_requirements from anon, authenticated;
revoke all privileges on table public.nexus_runtime_state from anon, authenticated;
revoke all privileges on table public.nexus_signals from anon, authenticated;

-- Remove direct privileges on current NEXUS-named sequences if present.
do $$
declare
  sequence_name text;
begin
  for sequence_name in
    select quote_ident(sequence_schema) || '.' || quote_ident(sequence_name)
    from information_schema.sequences
    where sequence_schema = 'public'
      and sequence_name like 'nexus_%'
  loop
    execute format('revoke all privileges on sequence %s from anon, authenticated', sequence_name);
  end loop;
end $$;

-- Future-safe defaults for objects created by postgres.
alter default privileges for role postgres in schema public
  revoke select, insert, update, delete, truncate, references, trigger on tables from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke execute on functions from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke usage, select, update on sequences from anon, authenticated;

-- Supabase-managed object creation has also shown public default ACLs under supabase_admin.
-- This block may require the executing role to have authority over supabase_admin. If it
-- fails, ROLLBACK and apply the equivalent setting through the authorized platform owner.
alter default privileges for role supabase_admin in schema public
  revoke select, insert, update, delete, truncate, references, trigger on tables from anon, authenticated;
alter default privileges for role supabase_admin in schema public
  revoke execute on functions from anon, authenticated;
alter default privileges for role supabase_admin in schema public
  revoke usage, select, update on sequences from anon, authenticated;

commit;
