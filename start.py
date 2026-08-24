from __future__ import annotations

import os
from pathlib import Path

import uvicorn

from canonical_sources import CanonicalStore


def main() -> None:
    store = CanonicalStore(Path(os.getenv("NEXUS_CANONICAL_DB", "/data/canonical.db")))
    source_dir = Path(os.getenv("NEXUS_CANONICAL_SOURCE_DIR", "/app/canonical_source_files"))
    if source_dir.is_dir():
        store.ingest_directory(source_dir)
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("PORT", "8421")), workers=1)


if __name__ == "__main__":
    main()

