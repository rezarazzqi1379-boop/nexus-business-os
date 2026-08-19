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
    source_version_ref: str
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
    checkpoint_id: str
    artifact_ref: str
    backend: str
    stored_artifact_ref: str
    stored_at: str
    source_version_ref: str
    source_content_sha256: str


@dataclass(frozen=True)
class RestoreProof:
    checkpoint_id: str
    artifact_ref: str
    backend: str
    stored_artifact_ref: str
    restored_artifact_ref: str
    restored_at: str
    source_version_ref: str
    expected_content_sha256: str
    restored_content_sha256: str


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


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def _timezone_error(name: str, value: object) -> str | None:
    meta_error = _meta_error(name, value)
    if meta_error:
        return meta_error
    assert isinstance(value, str)
    try:
        parsed = _parse_timestamp(value)
    except ValueError:
        return f"{name} must be ISO-8601"
    if parsed.tzinfo is None:
        return f"{name} must include a timezone offset"
    return None


def validate_checkpoint(manifest: CheckpointManifest) -> list[str]:
    if not isinstance(manifest, CheckpointManifest):
        return ["manifest must be a CheckpointManifest"]
    errors: list[str] = []
    for name, value in (("checkpoint_id", manifest.checkpoint_id), ("scope", manifest.scope), ("idempotency_key", manifest.idempotency_key)):
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
        for name, value in (("artifact_ref", entry.artifact_ref), ("source_ref", entry.source_ref), ("source_version_ref", entry.source_version_ref)):
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
    if not isinstance(receipt, BackupReceipt):
        return ["receipt must be a BackupReceipt"]
    errors: list[str] = []
    for name, value in (("checkpoint_id", receipt.checkpoint_id), ("artifact_ref", receipt.artifact_ref), ("backend", receipt.backend), ("stored_artifact_ref", receipt.stored_artifact_ref), ("source_version_ref", receipt.source_version_ref)):
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


def validate_restore_proof(proof: RestoreProof) -> list[str]:
    if not isinstance(proof, RestoreProof):
        return ["proof must be a RestoreProof"]
    errors: list[str] = []
    for name, value in (("checkpoint_id", proof.checkpoint_id), ("artifact_ref", proof.artifact_ref), ("backend", proof.backend), ("stored_artifact_ref", proof.stored_artifact_ref), ("restored_artifact_ref", proof.restored_artifact_ref), ("source_version_ref", proof.source_version_ref)):
        error = _meta_error(name, value)
        if error:
            errors.append(error)
    restored_at_error = _timezone_error("restored_at", proof.restored_at)
    if restored_at_error:
        errors.append(restored_at_error)
    for name, value in (("expected_content_sha256", proof.expected_content_sha256), ("restored_content_sha256", proof.restored_content_sha256)):
        digest_error = _sha256_error(value)
        if digest_error:
            errors.append(digest_error.replace("content_sha256", name))
    return errors


def receipt_covers_manifest_entry(receipt: BackupReceipt, manifest: CheckpointManifest) -> bool:
    if validate_backup_receipt(receipt) or validate_checkpoint(manifest):
        return False
    if receipt.checkpoint_id != manifest.checkpoint_id:
        return False
    if _parse_timestamp(receipt.stored_at) < _parse_timestamp(manifest.captured_at):
        return False
    matching = [entry for entry in manifest.entries if entry.artifact_ref == receipt.artifact_ref]
    if len(matching) != 1:
        return False
    entry = matching[0]
    return entry.source_version_ref == receipt.source_version_ref and entry.content_sha256 == receipt.source_content_sha256


def restore_proves_reconstruction(proof: RestoreProof, receipt: BackupReceipt, manifest: CheckpointManifest) -> bool:
    if validate_restore_proof(proof):
        return False
    if not receipt_covers_manifest_entry(receipt, manifest):
        return False
    if _parse_timestamp(proof.restored_at) < _parse_timestamp(receipt.stored_at):
        return False
    if proof.checkpoint_id != receipt.checkpoint_id or proof.artifact_ref != receipt.artifact_ref or proof.backend != receipt.backend or proof.stored_artifact_ref != receipt.stored_artifact_ref or proof.source_version_ref != receipt.source_version_ref or proof.expected_content_sha256 != receipt.source_content_sha256:
        return False
    return proof.restored_content_sha256 == proof.expected_content_sha256


def checkpoint_matches(manifest: CheckpointManifest, previous: CheckpointManifest | None) -> bool:
    if previous is None:
        return False
    if validate_checkpoint(manifest) or validate_checkpoint(previous):
        return False
    if manifest.idempotency_key != previous.idempotency_key:
        return False
    current = tuple((entry.artifact_ref, entry.source_ref, entry.source_version_ref, entry.category, entry.content_sha256) for entry in manifest.entries)
    prior = tuple((entry.artifact_ref, entry.source_ref, entry.source_version_ref, entry.category, entry.content_sha256) for entry in previous.entries)
    return current == prior


def changed_artifact_refs(manifest: CheckpointManifest, previous: CheckpointManifest | None) -> tuple[str, ...]:
    if validate_checkpoint(manifest):
        return ()
    previous_by_ref = {}
    if previous is not None and not validate_checkpoint(previous):
        previous_by_ref = {entry.artifact_ref: (entry.source_version_ref, entry.content_sha256) for entry in previous.entries}
    return tuple(entry.artifact_ref for entry in manifest.entries if previous_by_ref.get(entry.artifact_ref) != (entry.source_version_ref, entry.content_sha256))
