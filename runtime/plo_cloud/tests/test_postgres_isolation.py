import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from postgres_isolated import PostgresPLOStore, PLO_SCHEMA

DSN = os.environ["NEXUS_PLO_DATABASE_URL"]
os.environ["NEXUS_PLO_ALLOW_TEST_RESET"] = "1"


def test_schema_isolation():
    s = PostgresPLOStore(DSN)
    s.migrate()
    s.reset_for_tests()
    with s.connect() as conn:
        with conn.cursor() as cur:
            cur.execute("SHOW search_path")
            search_path = cur.fetchone()["search_path"].replace('"', '')
            assert search_path == f"{PLO_SCHEMA}, pg_catalog"
            assert "public" not in search_path
            cur.execute("SELECT current_schema() AS s")
            assert cur.fetchone()["s"] == PLO_SCHEMA
            cur.execute(
                "SELECT count(*) AS n FROM pg_tables WHERE schemaname=%s AND tablename LIKE %s",
                (PLO_SCHEMA, "plo_%"),
            )
            assert cur.fetchone()["n"] >= 5
            cur.execute(
                "SELECT count(*) AS n FROM pg_tables WHERE schemaname=%s AND tablename LIKE %s",
                ("public", "plo_%"),
            )
            assert cur.fetchone()["n"] == 0


def test_runtime_queries_use_isolated_schema():
    s = PostgresPLOStore(DSN)
    s.migrate()
    s.reset_for_tests()
    rid = s.enqueue("schema-test", "schema-isolation-key")
    claim = s.claim_next("schema-worker", 30)
    assert claim and claim["run_id"] == rid


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for test in tests:
        try:
            test(); print(test.__name__ + ": PASS")
        except Exception as exc:
            failed += 1; print(test.__name__ + f": FAIL {type(exc).__name__}: {exc}")
    print(f"\n{len(tests)-failed}/{len(tests)} PostgreSQL isolation tests passed")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
