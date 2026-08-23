import argparse, json, os
from plo_core import PLOStore


def run_once(db=None, backend="auto"):
    dsn = os.getenv("NEXUS_PLO_DATABASE_URL")
    selected = backend
    if selected == "auto":
        selected = "postgres" if dsn else "sqlite"

    if selected == "postgres":
        if not dsn:
            raise RuntimeError("NEXUS_PLO_DATABASE_URL is required for postgres backend")
        from postgres_store import PostgresPLOStore
        store = PostgresPLOStore(dsn)
        store.migrate()
        location = "postgres"
    elif selected == "sqlite":
        db = db or os.getenv("NEXUS_PLO_DB", "/data/nexus_plo.db")
        os.makedirs(os.path.dirname(os.path.abspath(db)), exist_ok=True)
        store = PLOStore(db)
        location = db
    else:
        raise RuntimeError(f"unsupported backend: {selected}")

    recovered = store.recover_orphans()
    return {
        "mode": "PLO_CLOUD_READ_ONLY",
        "backend": selected,
        "state_location": location,
        "gmail_write_enabled": False,
        "recovered": recovered,
        "metrics": store.metrics(),
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--db", default=os.getenv("NEXUS_PLO_DB", "/data/nexus_plo.db"))
    p.add_argument("--backend", choices=("auto", "sqlite", "postgres"), default="auto")
    a = p.parse_args()
    print(json.dumps(run_once(a.db, a.backend), indent=2))
