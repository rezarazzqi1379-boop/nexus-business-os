import psycopg
from psycopg.rows import dict_row

from postgres_store import PostgresPLOStore as _BasePostgresPLOStore, SCHEMA_SQL

PLO_SCHEMA = "nexus_plo"


class PostgresPLOStore(_BasePostgresPLOStore):
    """Schema-isolated PLO store.

    PLO execution state is intentionally kept out of public/business schemas.
    Runtime connections use only the dedicated nexus_plo schema. Schema creation
    remains an explicit migration/provisioning action; worker startup never runs DDL.
    """

    def connect(self):
        conn = psycopg.connect(self.dsn, row_factory=dict_row)
        conn.execute(f"SET search_path TO {PLO_SCHEMA}, public")
        return conn

    def migrate(self):
        # Migration path may create the dedicated schema; runtime workers must not
        # call this method and should use a role without CREATE privileges.
        with psycopg.connect(self.dsn, row_factory=dict_row) as conn:
            with conn.cursor() as cur:
                cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PLO_SCHEMA}")
                cur.execute(f"SET search_path TO {PLO_SCHEMA}, public")
                cur.execute(SCHEMA_SQL)
