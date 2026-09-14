"""Unified NEXUS data catalog and verified local backup snapshots.

Existing stores remain authoritative.  This hub indexes their locations and
cross-project observations so they can be queried and backed up together.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from contextlib import closing
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

AssetKind = Literal["sqlite", "json", "jsonl", "markdown", "document", "media", "transcript", "directory", "other"]
_BLOCKED_NAMES = {".env", ".env.production", "id_rsa", "id_ed25519", "credentials.json"}
_BLOCKED_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def _safe_relative(root: Path, path: Path) -> Path:
    root, path = root.resolve(), path.resolve()
    if path != root and root not in path.parents:
        raise ValueError("asset_outside_workspace")
    if path.is_symlink():
        raise ValueError("symlink_asset_not_allowed")
    return path.relative_to(root)


def _contains_secret_name(path: Path) -> bool:
    return path.name.casefold() in _BLOCKED_NAMES or path.suffix.casefold() in _BLOCKED_SUFFIXES


@dataclass(frozen=True)
class DataAsset:
    asset_id: str
    project_id: str
    kind: AssetKind
    relative_path: str
    authority: str
    contains_secrets: bool = False

    def validate(self) -> None:
        if not all(x.strip() for x in (self.asset_id, self.project_id, self.relative_path, self.authority)):
            raise ValueError("invalid_data_asset")
        if self.kind not in {"sqlite", "json", "jsonl", "markdown", "document", "media", "transcript", "directory", "other"}:
            raise ValueError("invalid_asset_kind")
        if Path(self.relative_path).is_absolute() or ".." in Path(self.relative_path).parts:
            raise ValueError("unsafe_asset_path")


@dataclass(frozen=True)
class EvidenceObservation:
    observation_id: str
    project_id: str
    category: str
    statement: str
    evidence_refs: tuple[str, ...]
    observed_at: str
    confidence: float

    def validate(self) -> None:
        if not all(x.strip() for x in (self.observation_id, self.project_id, self.category, self.statement)):
            raise ValueError("invalid_observation")
        if not self.evidence_refs or any(not ref.strip() for ref in self.evidence_refs):
            raise ValueError("observation_evidence_required")
        if not 0 <= self.confidence <= 1:
            raise ValueError("invalid_observation_confidence")
        parsed = datetime.fromisoformat(self.observed_at.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            raise ValueError("observation_time_requires_timezone")


class UnifiedDataHub:
    def __init__(self, path: Path, workspace_root: Path) -> None:
        self.path = path.resolve()
        self.workspace_root = workspace_root.resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self._connect()) as db:
            db.executescript("""
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS data_assets (
                    asset_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, kind TEXT NOT NULL,
                    relative_path TEXT NOT NULL, authority TEXT NOT NULL, contains_secrets INTEGER NOT NULL,
                    registered_at TEXT NOT NULL, UNIQUE(relative_path)
                );
                CREATE TABLE IF NOT EXISTS evidence_observations (
                    observation_id TEXT PRIMARY KEY, project_id TEXT NOT NULL, category TEXT NOT NULL,
                    statement TEXT NOT NULL, evidence_refs_json TEXT NOT NULL, observed_at TEXT NOT NULL,
                    confidence REAL NOT NULL, content_sha256 TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_observation_project ON evidence_observations(project_id, observed_at);
            """)
            db.commit()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
        db.row_factory = sqlite3.Row
        return db

    def register_asset(self, asset: DataAsset) -> bool:
        asset.validate()
        target = self.workspace_root / asset.relative_path
        _safe_relative(self.workspace_root, target)
        if not target.exists():
            raise FileNotFoundError(asset.relative_path)
        if asset.contains_secrets or _contains_secret_name(target):
            raise PermissionError("secret_asset_registration_denied")
        with closing(self._connect()) as db:
            try:
                db.execute("INSERT INTO data_assets VALUES (?,?,?,?,?,?,?)", (
                    asset.asset_id, asset.project_id, asset.kind, asset.relative_path,
                    asset.authority, 0, _utc_now(),
                ))
                db.commit()
                return True
            except sqlite3.IntegrityError:
                row = db.execute("SELECT * FROM data_assets WHERE asset_id=?", (asset.asset_id,)).fetchone()
                if row and all(row[key] == value for key, value in (
                    ("project_id", asset.project_id), ("kind", asset.kind),
                    ("relative_path", asset.relative_path), ("authority", asset.authority),
                )):
                    return False
                raise ValueError("data_asset_identity_collision")

    def record_observation(self, item: EvidenceObservation) -> bool:
        item.validate()
        refs = json.dumps(item.evidence_refs, ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.sha256(json.dumps(asdict(item), ensure_ascii=False, sort_keys=True).encode()).hexdigest()
        with closing(self._connect()) as db:
            try:
                db.execute("INSERT INTO evidence_observations VALUES (?,?,?,?,?,?,?,?)", (
                    item.observation_id, item.project_id, item.category, item.statement,
                    refs, item.observed_at, item.confidence, digest,
                ))
                db.commit()
                return True
            except sqlite3.IntegrityError:
                row = db.execute("SELECT content_sha256 FROM evidence_observations WHERE observation_id=?",
                                 (item.observation_id,)).fetchone()
                if row and row[0] == digest:
                    return False
                raise ValueError("observation_identity_collision")

    def project_view(self, project_id: str) -> tuple[dict, ...]:
        if not project_id.strip():
            raise ValueError("invalid_project_id")
        with closing(self._connect()) as db:
            rows = db.execute(
                "SELECT * FROM evidence_observations WHERE project_id=? ORDER BY observed_at, observation_id",
                (project_id,),
            ).fetchall()
        return tuple({**dict(row), "evidence_refs": tuple(json.loads(row["evidence_refs_json"]))} for row in rows)

    def assets(self) -> tuple[DataAsset, ...]:
        with closing(self._connect()) as db:
            rows = db.execute("SELECT * FROM data_assets ORDER BY asset_id").fetchall()
        return tuple(DataAsset(row["asset_id"], row["project_id"], row["kind"], row["relative_path"],
                               row["authority"], bool(row["contains_secrets"])) for row in rows)


@dataclass(frozen=True)
class BackupFile:
    asset_id: str
    relative_path: str
    size: int
    sha256: str


@dataclass(frozen=True)
class BackupManifest:
    schema_version: str
    snapshot_id: str
    created_at: str
    files: tuple[BackupFile, ...]


class BackupManager:
    def __init__(self, hub: UnifiedDataHub, backup_root: Path) -> None:
        self.hub = hub
        self.backup_root = backup_root.resolve()
        self.backup_root.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self, snapshot_id: str) -> Path:
        if not snapshot_id or not all(c.isalnum() or c in "-_" for c in snapshot_id):
            raise ValueError("invalid_snapshot_id")
        target = self.backup_root / snapshot_id
        if target.exists():
            raise FileExistsError("snapshot_already_exists")
        temporary = self.backup_root / f".{snapshot_id}.{uuid.uuid4().hex}.tmp"
        temporary.mkdir()
        files: list[BackupFile] = []
        try:
            assets = (DataAsset("nexus-data-hub", "NEXUS_CORE", "sqlite",
                                str(self.hub.path.relative_to(self.hub.workspace_root)), "unified-index"),
                      *self.hub.assets())
            for asset in assets:
                source = self.hub.workspace_root / asset.relative_path
                _safe_relative(self.hub.workspace_root, source)
                if asset.contains_secrets or _contains_secret_name(source):
                    continue
                for actual, relative in self._expand(source, Path(asset.relative_path)):
                    destination = temporary / "files" / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if asset.kind == "sqlite" and actual.is_file():
                        self._sqlite_backup(actual, destination)
                    else:
                        shutil.copy2(actual, destination)
                    files.append(BackupFile(asset.asset_id, relative.as_posix(), destination.stat().st_size,
                                            _digest(destination)))
            manifest = BackupManifest("nexus.backup-manifest.v1", snapshot_id, _utc_now(),
                                      tuple(sorted(files, key=lambda x: (x.relative_path, x.asset_id))))
            payload = {**asdict(manifest), "files": [asdict(x) for x in manifest.files]}
            manifest_path = temporary / "manifest.json"
            manifest_path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
                                     encoding="utf-8")
            os.replace(temporary, target)
            return target
        except Exception:
            shutil.rmtree(temporary, ignore_errors=True)
            raise

    @staticmethod
    def _expand(source: Path, relative: Path):
        if source.is_file():
            yield source, relative
            return
        for item in sorted(source.rglob("*")):
            if item.is_file() and not item.is_symlink() and not _contains_secret_name(item):
                yield item, relative / item.relative_to(source)

    @staticmethod
    def _sqlite_backup(source: Path, destination: Path) -> None:
        with closing(sqlite3.connect(f"file:{source.as_posix()}?mode=ro", uri=True)) as src:
            with closing(sqlite3.connect(destination)) as dst:
                src.backup(dst)

    @staticmethod
    def verify_snapshot(path: Path) -> bool:
        manifest_path = path / "manifest.json"
        if not manifest_path.is_file():
            return False
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        if data.get("schema_version") != "nexus.backup-manifest.v1":
            return False
        for item in data.get("files", []):
            candidate = (path / "files" / item["relative_path"]).resolve()
            files_root = (path / "files").resolve()
            if files_root not in candidate.parents or not candidate.is_file():
                return False
            if candidate.stat().st_size != item["size"] or _digest(candidate) != item["sha256"]:
                return False
        return True
