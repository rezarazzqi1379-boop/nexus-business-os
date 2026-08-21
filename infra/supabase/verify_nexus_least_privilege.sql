-- NEXUS least-privilege post-change verification (read-only)
-- Expected result after an approved hardening change: zero rows from each violation query.

-- Any remaining CRUD privilege on an internal NEXUS table is a violation.
with nexus_tables as (
  select c.oid, c.relname
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname like 'nexus_%'
)
select relname as table_name,
       has_table_privilege('anon', oid, 'SELECT') as anon_select,
       has_table_privilege('anon', oid, 'INSERT') as anon_insert,
       has_table_privilege('anon', oid, 'UPDATE') as anon_update,
       has_table_privilege('anon', oid, 'DELETE') as anon_delete,
       has_table_privilege('authenticated', oid, 'SELECT') as authenticated_select,
       has_table_privilege('authenticated', oid, 'INSERT') as authenticated_insert,
       has_table_privilege('authenticated', oid, 'UPDATE') as authenticated_update,
       has_table_privilege('authenticated', oid, 'DELETE') as authenticated_delete
from nexus_tables
where has_table_privilege('anon', oid, 'SELECT')
   or has_table_privilege('anon', oid, 'INSERT')
   or has_table_privilege('anon', oid, 'UPDATE')
   or has_table_privilege('anon', oid, 'DELETE')
   or has_table_privilege('authenticated', oid, 'SELECT')
   or has_table_privilege('authenticated', oid, 'INSERT')
   or has_table_privilege('authenticated', oid, 'UPDATE')
   or has_table_privilege('authenticated', oid, 'DELETE')
order by relname;

-- Current NEXUS-named sequences should not remain API-role accessible.
select sequence_schema,
       sequence_name,
       has_sequence_privilege('anon', format('%I.%I', sequence_schema, sequence_name), 'USAGE') as anon_usage,
       has_sequence_privilege('anon', format('%I.%I', sequence_schema, sequence_name), 'SELECT') as anon_select,
       has_sequence_privilege('authenticated', format('%I.%I', sequence_schema, sequence_name), 'USAGE') as authenticated_usage,
       has_sequence_privilege('authenticated', format('%I.%I', sequence_schema, sequence_name), 'SELECT') as authenticated_select
from information_schema.sequences
where sequence_schema = 'public'
  and sequence_name like 'nexus_%'
  and (
    has_sequence_privilege('anon', format('%I.%I', sequence_schema, sequence_name), 'USAGE')
    or has_sequence_privilege('anon', format('%I.%I', sequence_schema, sequence_name), 'SELECT')
    or has_sequence_privilege('authenticated', format('%I.%I', sequence_schema, sequence_name), 'USAGE')
    or has_sequence_privilege('authenticated', format('%I.%I', sequence_schema, sequence_name), 'SELECT')
  )
order by sequence_name;

-- Public functions should remain explicitly reviewed. Any API-role EXECUTE is surfaced.
select n.nspname as schema_name,
       p.proname as function_name,
       pg_get_function_identity_arguments(p.oid) as identity_args,
       p.prosecdef as security_definer,
       has_function_privilege('anon', p.oid, 'EXECUTE') as anon_execute,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') as authenticated_execute
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and (
    has_function_privilege('anon', p.oid, 'EXECUTE')
    or has_function_privilege('authenticated', p.oid, 'EXECUTE')
  )
order by p.proname, identity_args;

-- Default ACLs are displayed for human verification. API-role grants must not silently
-- reappear for postgres/supabase_admin-created public tables/functions/sequences.
select r.rolname as owner_role,
       n.nspname as schema_name,
       d.defaclobjtype,
       d.defaclacl as acl
from pg_default_acl d
join pg_roles r on r.oid = d.defaclrole
left join pg_namespace n on n.oid = d.defaclnamespace
where n.nspname = 'public'
  and r.rolname in ('postgres', 'supabase_admin')
order by owner_role, defaclobjtype;
