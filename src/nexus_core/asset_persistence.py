from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from .asset_memory import AssetRecord, validate_asset


@dataclass(frozen=True)
class PersistedAssetRef:
    asset_id: str
    backend: str
    storage_ref: str
    source_version_ref: str
    persisted_at: datetime


class AssetPersistence(Protocol):
    def put(self, asset: AssetRecord) -> PersistedAssetRef: ...
    def get(self, asset_id: str) -> AssetRecord | None: ...
    def list_project(self, project_ref: str) -> tuple[AssetRecord, ...]: ...


class InMemoryAssetPersistence:
    def __init__(self) -> None:
        self._items: dict[str, AssetRecord] = {}

    def put(self, asset: AssetRecord) -> PersistedAssetRef:
        errors = validate_asset(asset)
        if errors:
            raise ValueError(",".join(errors))
        current = self._items.get(asset.asset_id)
        if current and current.source_version_ref != asset.source_version_ref:
            raise ValueError("asset_id_version_collision")
        if current and current != asset:
            raise ValueError("asset_identity_collision")
        self._items[asset.asset_id] = asset
        return PersistedAssetRef(
            asset_id=asset.asset_id,
            backend="memory",
            storage_ref=f"memory://{asset.asset_id}",
            source_version_ref=asset.source_version_ref,
            persisted_at=asset.observed_at,
        )

    def get(self, asset_id: str) -> AssetRecord | None:
        return self._items.get(asset_id)

    def list_project(self, project_ref: str) -> tuple[AssetRecord, ...]:
        return tuple(a for a in self._items.values() if project_ref in a.project_refs)
