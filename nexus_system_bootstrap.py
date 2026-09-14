"""Bootstrap and activate the local governed NEXUS data environment."""

from __future__ import annotations

import argparse
import json
import os
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from portfolio_watchdog import watch_portfolio
from projects import PROJECTS
from unified_data_environment import BackupManager, DataAsset, UnifiedDataHub


def _atomic_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def _asset_kind(path: Path) -> str:
    if path.is_dir():
        return "directory"
    return {".db": "sqlite", ".json": "json", ".jsonl": "jsonl", ".md": "markdown",
            ".docx": "document"}.get(path.suffix.casefold(), "other")


def default_asset_paths(root: Path) -> tuple[Path, ...]:
    candidates = (
        root / "data" / "canonical.db",
        root / "data" / "state.db",
        root / "data" / "research",
        root / "data" / "operational",
        root / "research_lab",
        root / "canonical_source_files",
    )
    loose_data = tuple(sorted(p for p in (root / "data").glob("*.json") if p.is_file()))
    return tuple(p for p in (*candidates, *loose_data) if p.exists())


def activate(root: Path, *, snapshot_id: str | None = None) -> dict:
    root = root.resolve()
    system_root = root / "data" / "nexus_system"
    hub = UnifiedDataHub(system_root / "nexus.db", root)
    registered = []
    for index, path in enumerate(default_asset_paths(root), start=1):
        relative = path.relative_to(root).as_posix()
        asset_id = f"asset-{index:03d}"
        hub.register_asset(DataAsset(asset_id, "NEXUS_PORTFOLIO", _asset_kind(path), relative, "existing-store"))
        registered.append(relative)

    now = int(datetime.now(timezone.utc).timestamp())
    watch = watch_portfolio(PROJECTS.values(), (), now=now)
    watch_payload = {
        "schema_version": "nexus.portfolio-watch.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "neglected_projects": list(watch.neglected_projects),
        "running": list(watch.schedule.running),
        "queued": list(watch.schedule.queued),
        "waiting": list(watch.schedule.waiting),
        "coverage": list(watch.coverage),
    }
    _atomic_json(system_root / "portfolio_watch.json", watch_payload)
    watch_asset = DataAsset("portfolio-watch", "NEXUS_PORTFOLIO", "json",
                            "data/nexus_system/portfolio_watch.json", "derived-read-model")
    hub.register_asset(watch_asset)

    chosen_snapshot = snapshot_id or datetime.now(timezone.utc).strftime("bootstrap-%Y%m%dT%H%M%SZ")
    snapshot = BackupManager(hub, system_root / "backups").create_snapshot(chosen_snapshot)
    verified = BackupManager.verify_snapshot(snapshot)
    if not verified:
        raise RuntimeError("bootstrap_snapshot_verification_failed")
    status = {
        "schema_version": "nexus.system-activation.v1",
        "activated_at": datetime.now(timezone.utc).isoformat(),
        "hub": str(hub.path.relative_to(root).as_posix()),
        "registered_assets": registered,
        "portfolio_projects": len(PROJECTS),
        "portfolio_coverage": len(watch.coverage),
        "snapshot": str(snapshot.relative_to(root).as_posix()),
        "snapshot_verified": True,
        "external_actions_enabled": False,
    }
    _atomic_json(system_root / "activation_status.json", status)
    return status


def main() -> None:
    parser = argparse.ArgumentParser(description="Activate the local NEXUS data hub and verified backup.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--snapshot-id")
    args = parser.parse_args()
    print(json.dumps(activate(args.root, snapshot_id=args.snapshot_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

