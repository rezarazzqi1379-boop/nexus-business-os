from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from unicodedata import category


SnapshotCategory = Literal[
    "code",
    "decision",
    "evidence",
    "research",
    "commercial",
    "configuration",
    "documentation",
]
_ALLOWED_CATEGORIES = {
    "code",
    "decision",
    "evidence",
    "research",
    "commercial",
    "configuration",
    "documentation",
}
_MAX_META_LENGTH = 256
_DISALLOWED_UNICODE_CATEGORIES = {"Cc", "Cf", "Zl", "Zp"}


@dataclass(frozen=True)
class SnapshotEntry:
    artifact_ref: str
    source_ref: str
    category: SnapshotCategory
    content_sha256: str


@dataclass(frozen=True)
class CheckpointManifest:
    checkpoint_id: str
    scope: str
    captured_at: str
    idempotency_key: str
    entries: tuple[SnapshotEntry, ...]


@dataclass(frozen=True)
class BackupReceipt:
    """Evidence that one checkpoint artifact was written to a storage backend.

    The receipt is intentionally metadata-only. It proves the destination reference and
    the source-content digest that was claimed at write time; it does not make the
    backend canonical NEXUS state and it does not authorize restore or deletion.
    """

    checkpoint_id: str
    artifact_ref: str
    backend: str
    stored_artifact_ref: str
    stored_at: str
    source_content_sha256: str


def _meta_error(name: str, value: object) -> str | None:
    if not isinstance(value, str):
        return f"{name} must be a string"
    if not value.strip():
        return f"{name} is required"
    if value != value.strip():
        return f"{name} cannot have leading or trailing whitespace"
    if len(value) > _MAX_META_LENGTH:
        return f"{name} must be at most {_MAX_META_LENGTH} characters"
    if any(category(ch) in _DISALLOWED_UNICODE_CATEGORIES for ch in value):
        return f"{name} cannot contain control or formatting characters"
    return None


def _sha256_error(value: object) -> str | None:
    if not isinstance(value, str):
        return "content_sha256 must be a string"
    if len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
        return "content_sha256 must be a lowercase 64-character SHA-256 hex digest"
    return None


def _timezone_error(name: str, value: object) -> str | None:
    meta_error = _meta_error(name, value)
    if meta_error:
        return meta_error
    assert isinstance(value, str)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return f"{name} must be ISO-8601"
    if parsed.tzinfo is None:
        return f"{name} must include a timezone offset"
    return None


def validate_checkpoint(manifest: CheckpointManifest) -> list[str]:
    """Validate backup metadata without assuming any storage backend."""
    if not isinstance(manifest, CheckpointManifest):
        return ["manifest must be a CheckpointManifest"]

    errors: list[str] = []
    for name, value in (
        ("checkpoint_id", manifest.checkpoint_id),
        ("scope", manifest.scope),
        ("idempotency_key", manifest.idempotency_key),
    ):
        error = _meta_error(name, value)
        if error:
            errors.append(error)

    captured_error = _timezone_error("captured_at", manifest.captured_at)
    if captured_error:
        errors.append(captured_error)

    if not isinstance(manifest.entries, tuple):
        return errors + ["entries must be a tuple"]
    if not manifest.entries:
        errors.append("entries requires at least one snapshot entry")
        return errors

    seen_artifacts: set[str] = set()
    for entry in manifest.entries:
        if not isinstance(entry, SnapshotEntry):
            errors.append("entries must contain SnapshotEntry values")
            continue
        for name, value in (
            ("artifact_ref", entry.artifact_ref),
            ("source_ref", entry.source_ref),
        ):
            error = _meta_error(name, value)
            if error:
                errors.append(error)
        if not isinstance(entry.category, str) or entry.category not in _ALLOWED_CATEGORIES:
            errors.append("snapshot category must be supported")
        digest_error = _sha256_error(entry.content_sha256)
        if digest_error:
            errors.append(digest_error)
        if isinstance(entry.artifact_ref, str):
            if entry.artifact_ref in seen_artifacts:
                errors.append("checkpoint cannot contain duplicate artifact_ref values")
            seen_artifacts.add(entry.artifact_ref)

    return errors


def validate_backup_receipt(receipt: BackupReceipt) -> list[str]:
    """Fail closed on ambiguous or malformed storage-write evidence."""
    if not isinstance(receipt, BackupReceipt):
        return ["receipt must be a BackupReceipt"]

    errors: list[str] = []
    for name, value in (
        ("checkpoint_id", receipt.checkpoint_id),
        ("artifact_ref", receipt.artifact_ref),
        ("backend", receipt.backend),
        ("stored_artifact_ref", receipt.stored_artifact_ref),
    ):
        error = _meta_error(name, value)
        if error:
            errors.append(error)

    stored_at_error = _timezone_error("stored_at", receipt.stored_at)
    if stored_at_error:
        errors.append(stored_at_error)

    digest_error = _sha256_error(receipt.source_content_sha256)
    if digest_error:
        errors.append(digest_error.replace("content_sha256", "source_content_sha256"))
    return errors


def receipt_covers_manifest_entry(
    receipt: BackupReceipt,
    manifest: CheckpointManifest,
) -> bool:
    """True only when storage evidence matches an exact manifest entry digest."""
    if validate_backup_receipt(receipt) or validate_checkpoint(manifest):
        return False
    if receipt.checkpoint_id != manifest.checkpoint_id:
        return False
    matching = [entry for entry in manifest.entries if entry.artifact_ref == receipt.artifact_ref]
    if len(matching) != 1:
        return False
    return matching[0].content_sha256 == receipt.source_content_sha256


def checkpoint_matches(
    manifest: CheckpointManifest,
    previous: CheckpointManifest | None,
) -> bool:
    """Return True only when the same idempotency key represents identical snapshot content."""
    if previous is None:
        return False
    if validate_checkpoint(manifest) or validate_checkpoint(previous):
        return False
    if manifest.idempotency_key != previous.idempotency_key:
        return False
    current = tuple(
        (entry.artifact_ref, entry.source_ref, entry.category, entry.content_sha256)
        for entry in manifest.entries
    )
    prior = tuple(
        (entry.artifact_ref, entry.source_ref, entry.category, entry.content_sha256)
        for entry in previous.entries
    )
    return current == prior


def changed_artifact_refs(
    manifest: CheckpointManifest,
    previous: CheckpointManifest | None,
) -> tuple[str, ...]:
    """Identify changed/new artifacts for incremental backup without deleting old snapshots."""
    if validate_checkpoint(manifest):
        return ()
    previous_by_ref = {}
    if previous is not None and not validate_checkpoint(previous):
        previous_by_ref = {entry.artifact_ref: entry.content_sha256 for entry in previous.entries}
    changed = [
        entry.artifact_ref
        for entry in manifest.entries
        if previous_by_ref.get(entry.artifact_ref) != entry.content_sha256
    ]
    return tuple(changed)
