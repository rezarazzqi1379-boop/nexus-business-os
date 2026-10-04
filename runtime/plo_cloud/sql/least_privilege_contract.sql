-- NEXUS PLO v0.3 least-privilege deployment contract
-- Run provisioning with an explicit migration/admin role. Do NOT execute this
-- from the runtime worker. Replace role names/password handling in the target
-- environment; this file documents the required privilege boundary.

CREATE SCHEMA IF NOT EXISTS nexus_plo;

-- Example roles (creation may be handled by the hosting platform instead):
-- CREATE ROLE nexus_plo_migrator NOLOGIN;
-- CREATE ROLE nexus_plo_runtime NOLOGIN;

-- Migrator owns/updates schema objects during controlled promotion only.
-- GRANT USAGE, CREATE ON SCHEMA nexus_plo TO nexus_plo_migrator;

-- Runtime can use existing objects but cannot create/alter/drop schema objects.
-- GRANT USAGE ON SCHEMA nexus_plo TO nexus_plo_runtime;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA nexus_plo TO nexus_plo_runtime;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA nexus_plo TO nexus_plo_runtime;
-- ALTER DEFAULT PRIVILEGES FOR ROLE nexus_plo_migrator IN SCHEMA nexus_plo
--   GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO nexus_plo_runtime;
-- ALTER DEFAULT PRIVILEGES FOR ROLE nexus_plo_migrator IN SCHEMA nexus_plo
--   GRANT USAGE, SELECT ON SEQUENCES TO nexus_plo_runtime;

-- Explicitly do not grant CREATE on schema/public, role administration,
-- database ownership, RLS/ACL administration, or access to NEXUS business
-- authority tables to the runtime role. PLO is an execution substrate only.
