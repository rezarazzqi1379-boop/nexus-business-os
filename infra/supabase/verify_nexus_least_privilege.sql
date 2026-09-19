-- NEXUS least-privilege post-change verification (read-only)
-- Expected result after an approved hardening change: zero rows from EACH violation query.
--
-- Forge regression target (2026-08-23): a previous hardening pass successfully revoked
-- privileges from the then-existing 17 tables, but later-created NEXUS relations inherited
-- API-role grants. Verification must therefore cover both CURRENT objects and FUTURE defaults.

-- 1) Any remaining CRUD privilege on an internal NEXUS base table is a violation.
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

-- 2) Current NEXUS-named sequences should not remain API-role accessible.
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

-- 3) Public functions should remain explicitly reviewed. Any API-role EXECUTE is surfaced.
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

-- 4) FUTURE-OBJECT REGRESSION GUARD.
-- Any default ACL entry that grants anon/authenticated privileges for public-schema objects
-- owned by postgres/supabase_admin is a violation. This is the recurrence class that allowed
-- newer NEXUS relations to regain grants after the first 17-table revoke.
select owner_role.rolname as owner_role,
       n.nspname as schema_name,
       d.defaclobjtype,
       grantee_role.rolname as grantee,
       x.privilege_type,
       x.is_grantable
from pg_default_acl d
join pg_roles owner_role on owner_role.oid = d.defaclrole
left join pg_namespace n on n.oid = d.defaclnamespace
cross join lateral aclexplode(d.defaclacl) x
left join pg_roles grantee_role on grantee_role.oid = x.grantee
where n.nspname = 'public'
  and owner_role.rolname in ('postgres', 'supabase_admin')
  and grantee_role.rolname in ('anon', 'authenticated')
order by owner_role, d.defaclobjtype, grantee, x.privilege_type;

-- 5) Inventory / policy context for human review. This query is informational and is NOT
-- itself expected to return zero rows.
select c.relname as table_name,
       c.relrowsecurity as rls_enabled,
       (select count(*) from pg_policy p where p.polrelid = c.oid) as policy_count
from pg_class c
join pg_namespace n on n.oid = c.relnamespace
where n.nspname = 'public'
  and c.relkind = 'r'
  and c.relname like 'nexus_%'
order by c.relname;