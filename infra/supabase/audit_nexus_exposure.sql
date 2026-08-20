-- NEXUS Supabase exposure audit (read-only)
-- Safe to run in SQL Editor. This file performs no DDL/DML writes.

with nexus_tables as (
  select c.oid,
         n.nspname as schema_name,
         c.relname as table_name,
         c.relrowsecurity as rls_enabled,
         pg_get_userbyid(c.relowner) as owner_role
  from pg_class c
  join pg_namespace n on n.oid = c.relnamespace
  where n.nspname = 'public'
    and c.relkind = 'r'
    and c.relname like 'nexus_%'
)
select schema_name,
       table_name,
       owner_role,
       rls_enabled,
       has_table_privilege('anon', oid, 'SELECT') as anon_select,
       has_table_privilege('anon', oid, 'INSERT') as anon_insert,
       has_table_privilege('anon', oid, 'UPDATE') as anon_update,
       has_table_privilege('anon', oid, 'DELETE') as anon_delete,
       has_table_privilege('authenticated', oid, 'SELECT') as authenticated_select,
       has_table_privilege('authenticated', oid, 'INSERT') as authenticated_insert,
       has_table_privilege('authenticated', oid, 'UPDATE') as authenticated_update,
       has_table_privilege('authenticated', oid, 'DELETE') as authenticated_delete,
       (select count(*) from pg_policy p where p.polrelid = nexus_tables.oid) as policy_count
from nexus_tables
order by table_name;

-- Public-schema functions/RPCs and EXECUTE exposure.
select n.nspname as schema_name,
       p.proname as function_name,
       pg_get_function_identity_arguments(p.oid) as identity_args,
       p.prosecdef as security_definer,
       has_function_privilege('anon', p.oid, 'EXECUTE') as anon_execute,
       has_function_privilege('authenticated', p.oid, 'EXECUTE') as authenticated_execute,
       has_function_privilege('service_role', p.oid, 'EXECUTE') as service_role_execute
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
order by p.proname, identity_args;

-- Default privileges that can auto-expose future tables/functions/sequences.
select r.rolname as owner_role,
       n.nspname as schema_name,
       d.defaclobjtype,
       d.defaclacl as acl
from pg_default_acl d
join pg_roles r on r.oid = d.defaclrole
left join pg_namespace n on n.oid = d.defaclnamespace
where n.nspname = 'public'
order by owner_role, defaclobjtype;
