import os, sys, uuid

import psycopg
from psycopg import errors

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from postgres_isolated import PostgresPLOStore, PLO_SCHEMA

DSN = os.environ["NEXUS_PLO_DATABASE_URL"]
ROLE = "nexus_plo_runtime_ci"


def main():
    store = PostgresPLOStore(DSN)
    store.migrate()

    with psycopg.connect(DSN, autocommit=True) as admin:
        admin.execute(f"DROP ROLE IF EXISTS {ROLE}")
        admin.execute(f"CREATE ROLE {ROLE} NOLOGIN")
        admin.execute(f"GRANT USAGE ON SCHEMA {PLO_SCHEMA} TO {ROLE}")
        admin.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {PLO_SCHEMA} TO {ROLE}")
        admin.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {PLO_SCHEMA} TO {ROLE}")

        admin.execute(f"SET ROLE {ROLE}")
        admin.execute(f"SET search_path TO {PLO_SCHEMA}, public")
        admin.execute("SELECT count(*) FROM plo_tasks")
        rid = str(uuid.uuid4())
        admin.execute(
            "INSERT INTO plo_tasks(run_id,task_id,idempotency_key,status,approval_required) VALUES(%s::uuid,%s,%s,'PENDING',false)",
            (rid, "least-privilege", "least-privilege-" + rid),
        )
        admin.execute("DELETE FROM plo_tasks WHERE run_id=%s::uuid", (rid,))

        blocked_schema_ddl = False
        try:
            admin.execute(f"CREATE TABLE {PLO_SCHEMA}.runtime_must_not_create(id int)")
        except errors.InsufficientPrivilege:
            blocked_schema_ddl = True
        assert blocked_schema_ddl, "runtime role unexpectedly created table in nexus_plo"

        blocked_public_ddl = False
        try:
            admin.execute("CREATE TABLE public.runtime_must_not_create(id int)")
        except errors.InsufficientPrivilege:
            blocked_public_ddl = True
        assert blocked_public_ddl, "runtime role unexpectedly created table in public"

        admin.execute("RESET ROLE")
        # The runtime role owns no objects, but GRANTs create dependency records.
        # Revoke/drop those test-only privileges before removing the ephemeral CI role.
        admin.execute(f"DROP OWNED BY {ROLE}")
        admin.execute(f"DROP ROLE {ROLE}")

    print("least_privilege_runtime_role: PASS")


if __name__ == "__main__":
    main()
