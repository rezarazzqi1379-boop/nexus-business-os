from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import tarfile
from datetime import datetime, timezone
from pathlib import Path


def backup(data_dir: Path, output_dir: Path) -> dict:
    data_dir, output_dir = data_dir.resolve(), output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = output_dir / f"nexus-backup-{stamp}"
    target.mkdir(mode=0o700)
    files = []
    for source in sorted(data_dir.glob("*.db")):
        destination = target / source.name
        with sqlite3.connect(source) as source_db, sqlite3.connect(destination) as destination_db:
            source_db.backup(destination_db)
            integrity = destination_db.execute("PRAGMA integrity_check").fetchone()[0]
        if integrity != "ok":
            raise RuntimeError("backup_integrity_failed")
        files.append(destination)
    vault = data_dir / "nexus_vault"
    if vault.exists():
        archive = target / "nexus_vault.tar.gz"
        with tarfile.open(archive, "w:gz") as tar:
            tar.add(vault, arcname="nexus_vault")
        files.append(archive)
    manifest = {"schema_version": "nexus.backup.v1", "created_at": datetime.now(timezone.utc).isoformat(),
                "files": {item.name: hashlib.sha256(item.read_bytes()).hexdigest() for item in files}}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {"backup": str(target), "file_count": len(files), "verified": True}


def verify_backup(path: Path) -> dict:
    manifest = json.loads((path.resolve() / "manifest.json").read_text(encoding="utf-8"))
    mismatches = []
    for name, expected in manifest["files"].items():
        item = path.resolve() / name
        actual = hashlib.sha256(item.read_bytes()).hexdigest() if item.is_file() else "missing"
        if actual != expected:
            mismatches.append(name)
    return {"valid": not mismatches, "mismatches": mismatches, "file_count": len(manifest["files"])}


def restore_backup(path: Path, destination: Path) -> dict:
    """Restore a verified backup into a new, empty directory.

    Refusing a non-empty target makes rollback explicit and prevents accidental
    overwrites of a running instance.
    """
    path, destination = path.resolve(), destination.resolve()
    verification = verify_backup(path)
    if not verification["valid"]:
        raise ValueError("backup_verification_failed")
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("restore_destination_not_empty")
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    restored = []
    for database in sorted(path.glob("*.db")):
        target = destination / database.name
        with sqlite3.connect(database) as source_db, sqlite3.connect(target) as target_db:
            source_db.backup(target_db)
            if target_db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise RuntimeError("restored_database_integrity_failed")
        restored.append(target.name)
    archive = path / "nexus_vault.tar.gz"
    if archive.is_file():
        with tarfile.open(archive, "r:gz") as tar:
            root = destination.resolve()
            for member in tar.getmembers():
                resolved = (destination / member.name).resolve()
                if root not in resolved.parents and resolved != root:
                    raise ValueError("unsafe_backup_archive_path")
                if member.issym() or member.islnk() or member.isdev():
                    raise ValueError("unsafe_backup_archive_member")
            tar.extractall(destination, filter="data")
        restored.append("nexus_vault")
    return {"restored": True, "destination": str(destination), "items": restored}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("backup")
    create.add_argument("--data-dir", default=os.getenv("NEXUS_DATA_DIR", "/data"))
    create.add_argument("--output-dir", required=True)
    check = sub.add_parser("verify-backup")
    check.add_argument("path")
    restore = sub.add_parser("restore-backup")
    restore.add_argument("path")
    restore.add_argument("--destination", required=True)
    args = parser.parse_args(argv)
    if args.command == "backup":
        result = backup(Path(args.data_dir), Path(args.output_dir))
    elif args.command == "verify-backup":
        result = verify_backup(Path(args.path))
    else:
        result = restore_backup(Path(args.path), Path(args.destination))
    print(json.dumps(result, indent=2))
    return 0 if result.get("valid", result.get("verified", False)) else 2


if __name__ == "__main__":
    raise SystemExit(main())
