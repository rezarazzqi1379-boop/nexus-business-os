from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from canonical_sources import CanonicalStore


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_dir", type=Path)
    parser.add_argument("--db", type=Path, default=Path(os.getenv("NEXUS_CANONICAL_DB", "/data/canonical.db")))
    args = parser.parse_args()
    print(json.dumps(CanonicalStore(args.db).ingest_directory(args.source_dir), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
