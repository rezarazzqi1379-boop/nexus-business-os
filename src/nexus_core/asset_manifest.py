from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Iterable

from .asset_memory import AssetRecord, validate_asset

CopyState = Literal["reference_only", "copied_unverified", "copied_verified", "copy_failed", "not_applicable"]
_ALLOWED_COPY_STATES = {"reference_only", "copied_unverified", "copied_verified", "copy_failed", "not_applicable"}


@dataclass(frozen=True)
class AssetBackupState:
    asset_id: str
    source_version_ref: str
    copy_state: CopyState
    backend_ref: str | None
    copied_at: datetime | None
    verified_at: datetime | None
    expected_sha256: str | None = None
    restored_sha256: str | None = None


@dataclass(frozen=True)
class AssetManifestEntry:
    asset: AssetRecord
    backup: AssetBackupState


@dataclass(frozen=True)
class AssetManifest:
    manifest_id: str
    created_at: datetime
    entries: tuple[AssetManifestEntry, ...]


def _valid_sha(value: str | None) -> bool:
    if value is None:
        return True
    return len(value) == 64 and all(c in "0123456789abcdef" for c in value.lower())


def validate_backup_state(state: AssetBackupState) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(state, AssetBackupState):
        return ("backup_state_must_be_asset_backup_state",)
    if not isinstance(state.asset_id, str) or not state.asset_id.strip():
        errors.append("invalid_asset_id")
    if not isinstance(state.source_version_ref, str) or not state.source_version_ref.strip():
        errors.append("invalid_source_version_ref")
    if state.copy_state not in _ALLOWED_COPY_STATES:
        errors.append("unsupported_copy_state")
    for name, value in (("copied_at", state.copied_at), ("verified_at", state.verified_at)):
        if value is not None and value.tzinfo is None:
            errors.append(f"timezone_naive_{name}")
    if state.copied_at and state.verified_at and state.verified_at < state.copied_at:
        errors.append("verified_before_copied")
    if not _valid_sha(state.expected_sha256):
        errors.append("invalid_expected_sha256")
    if not _valid_sha(state.restored_sha256):
        errors.append("invalid_restored_sha256")

    if state.copy_state == "reference_only":
        if state.backend_ref is not None or state.copied_at is not None or state.verified_at is not None:
            errors.append("reference_only_cannot_claim_copy")
    elif state.copy_state == "copied_unverified":
        if not state.backend_ref or state.copied_at is None:
            errors.append("copied_unverified_requires_backend_and_time")
        if state.verified_at is not None:
            errors.append("copied_unverified_cannot_have_verified_at")
    elif state.copy_state == "copied_verified":
        if not state.backend_ref or state.copied_at is None or state.verified_at is None:
            errors.append("copied_verified_requires_backend_and_times")
        if not state.expected_sha256 or not state.restored_sha256:
            errors.append("copied_verified_requires_digests")
        elif state.expected_sha256.lower() != state.restored_sha256.lower():
            errors.append("restore_digest_mismatch")
    elif state.copy_state == "copy_failed":
        if not state.backend_ref:
            errors.append("copy_failed_requires_backend_ref")
        if state.verified_at is not None:
            errors.append("copy_failed_cannot_be_verified")
    return tuple(errors)


def build_asset_manifest(manifest_id: str, created_at: datetime, entries: Iterable[AssetManifestEntry]) -> AssetManifest:
    if not isinstance(manifest_id, str) or not manifest_id.strip():
        raise ValueError("invalid_manifest_id")
    if created_at.tzinfo is None:
        raise ValueError("timezone_naive_created_at")
    items = tuple(entries)
    seen: set[str] = set()
    for entry in items:
        if not isinstance(entry, AssetManifestEntry):
            raise ValueError("entry_must_be_asset_manifest_entry")
        asset_errors = validate_asset(entry.asset)
        backup_errors = validate_backup_state(entry.backup)
        if asset_errors or backup_errors:
            raise ValueError(",".join((*asset_errors, *backup_errors)))
        if entry.asset.asset_id != entry.backup.asset_id:
            raise ValueError("asset_backup_identity_mismatch")
        if entry.asset.source_version_ref != entry.backup.source_version_ref:
            raise ValueError("asset_backup_version_mismatch")
        if entry.asset.asset_id in seen:
            raise ValueError("duplicate_asset_id")
        seen.add(entry.asset.asset_id)
        if entry.asset.content_sha256 and entry.backup.expected_sha256:
            if entry.asset.content_sha256.lower() != entry.backup.expected_sha256.lower():
                raise ValueError("asset_expected_digest_mismatch")
    return AssetManifest(manifest_id, created_at, items)


def verified_copy(asset_id: str, manifest: AssetManifest) -> bool:
    for entry in manifest.entries:
        if entry.asset.asset_id == asset_id:
            return entry.backup.copy_state == "copied_verified" and not validate_backup_state(entry.backup)
    return False
