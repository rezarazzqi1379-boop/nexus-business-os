-- NEXUS least-privilege hardening migration
-- STATUS: REVIEWED ARTIFACT ONLY / NOT APPLIED IN THIS FORGE PASS
-- Human Gate required before production execution.
--
-- Forge lesson (2026-08-23): a prior production hardening pass revoked grants from the
-- 17 then-existing NEXUS tables, but later-created NEXUS relations inherited broad
-- anon/authenticated privileges again. The old 17 remain revoked; newer relations drifted.
-- Therefore current-object cleanup alone is insufficient. This artifact revokes all
-- current NEXUS base-table privileges dynamically AND hardens future default privileges.
-- It intentionally does not create user-scoped RLS policies because the current schema
-- has no proven shared ownership/tenant key.

begin;

-- Fail closed if reviewed inventory or RLS-policy state changed.
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

  if nexus_table_count <> 30 then
    raise exception 'NEXUS table inventory drifted: expected reviewed count 30, found %; rerun audit before hardening', nexus_table_count;
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

-- Revoke current NEXUS base-table privileges dynamically so newly-added reviewed tables
-- are not omitted by a stale hardcoded list.
do $$
declare
  qualified_table text;
begin
  for qualified_table in
    select quote_ident(n.nspname) || '.' || quote_ident(c.relname)
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
    where n.nspname = 'public'
      and c.relkind = 'r'
      and c.relname like 'nexus_%'
    order by c.relname
  loop
    execute format(
      'revoke all privileges on table %s from anon, authenticated',
      qualified_table
    );
  end loop;
end $$;

-- Remove direct privileges on current NEXUS-named sequences if present.
do $$
declare
  qualified_sequence text;
begin
  for qualified_sequence in
    select quote_ident(s.sequence_schema) || '.' || quote_ident(s.sequence_name)
    from information_schema.sequences s
    where s.sequence_schema = 'public'
      and s.sequence_name like 'nexus_%'
  loop
    execute format(
      'revoke all privileges on sequence %s from anon, authenticated',
      qualified_sequence
    );
  end loop;
end $$;

-- Future-safe defaults for objects created by postgres. This is the critical recurrence
-- guard learned from the observed 17-table -> 30-table privilege drift.
alter default privileges for role postgres in schema public
  revoke select, insert, update, delete, truncate, references, trigger on tables from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke execute on functions from anon, authenticated;
alter default privileges for role postgres in schema public
  revoke usage, select, update on sequences from anon, authenticated;

-- Supabase-managed object creation may also use supabase_admin. These statements require
-- authority over that role. If unavailable, the transaction must fail/rollback rather
-- than silently leave future defaults unsafe.
alter default privileges for role supabase_admin in schema public
  revoke select, insert, update, delete, truncate, references, trigger on tables from anon, authenticated;
alter default privileges for role supabase_admin in schema public
  revoke execute on functions from anon, authenticated;
alter default privileges for role supabase_admin in schema public
  revoke usage, select, update on sequences from anon, authenticated;

commit;