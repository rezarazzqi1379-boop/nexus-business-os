from datetime import datetime, timedelta, timezone

from hypothesis import given, strategies as st

from nexus_core.checkpoints import (
    BackupReceipt,
    CheckpointManifest,
    RestoreProof,
    SnapshotEntry,
    changed_artifact_refs,
    checkpoint_matches,
    receipt_covers_manifest_entry,
    restore_proves_reconstruction,
    validate_backup_receipt,
    validate_checkpoint,
    validate_restore_proof,
)


HASH_A = "a" * 64
HASH_B = "b" * 64
VERSION_A = "notion:page:command-center:version:1"
VERSION_B = "notion:page:command-center:version:2"


def manifest(
    *,
    digest: str = HASH_A,
    captured_at: str = "2026-08-19T16:00:00+00:00",
    source_version_ref: str = VERSION_A,
):
    return CheckpointManifest(
        checkpoint_id="checkpoint:nexus:command-center",
        scope="nexus-command-center",
        captured_at=captured_at,
        idempotency_key="backup:nexus-command-center:v1",
        entries=(
            SnapshotEntry(
                artifact_ref="notion:command-center",
                source_ref="notion:page:command-center",
                source_version_ref=source_version_ref,
                category="documentation",
                content_sha256=digest,
            ),
        ),
    )


def receipt(
    *,
    digest: str = HASH_A,
    stored_at: str = "2026-08-19T19:44:00+03:30",
    source_version_ref: str = VERSION_A,
):
    return BackupReceipt(
        checkpoint_id="checkpoint:nexus:command-center",
        artifact_ref="notion:command-center",
        backend="google_drive",
        stored_artifact_ref="drive:file:example-backup-doc",
        stored_at=stored_at,
        source_version_ref=source_version_ref,
        source_content_sha256=digest,
    )


def restore_proof(
    *,
    expected_digest: str = HASH_A,
    restored_digest: str = HASH_A,
    restored_at: str = "2026-08-19T20:00:00+03:30",
    source_version_ref: str = VERSION_A,
    backend: str = "google_drive",
    stored_artifact_ref: str = "drive:file:example-backup-doc",
):
    return RestoreProof(
        checkpoint_id="checkpoint:nexus:command-center",
        artifact_ref="notion:command-center",
        backend=backend,
        stored_artifact_ref=stored_artifact_ref,
        restored_artifact_ref="restore:test:command-center",
        restored_at=restored_at,
        source_version_ref=source_version_ref,
        expected_content_sha256=expected_digest,
        restored_content_sha256=restored_digest,
    )


def test_valid_checkpoint_manifest_passes():
    assert validate_checkpoint(manifest()) == []


def test_checkpoint_requires_timezone_aware_capture_time():
    errors = validate_checkpoint(manifest(captured_at="2026-08-19T16:00:00"))
    assert "captured_at must include a timezone offset" in errors


def test_invalid_digest_fails_closed():
    errors = validate_checkpoint(manifest(digest="not-a-digest"))
    assert "content_sha256 must be a lowercase 64-character SHA-256 hex digest" in errors


def test_source_version_ref_is_required():
    errors = validate_checkpoint(manifest(source_version_ref=""))
    assert "source_version_ref is required" in errors


def test_same_idempotency_key_same_source_version_and_same_content_is_a_match():
    first = manifest()
    second = manifest(captured_at="2026-08-19T17:00:00+00:00")
    assert checkpoint_matches(second, first) is True


def test_changed_content_is_detected_for_incremental_backup():
    first = manifest(digest=HASH_A)
    second = manifest(digest=HASH_B)
    assert checkpoint_matches(second, first) is False
    assert changed_artifact_refs(second, first) == ("notion:command-center",)


def test_new_source_version_is_changed_even_when_digest_is_identical():
    first = manifest(digest=HASH_A, source_version_ref=VERSION_A)
    second = manifest(digest=HASH_A, source_version_ref=VERSION_B)
    assert checkpoint_matches(second, first) is False
    assert changed_artifact_refs(second, first) == ("notion:command-center",)


def test_duplicate_artifact_refs_are_rejected():
    duplicate = CheckpointManifest(
        checkpoint_id="checkpoint:test",
        scope="test",
        captured_at="2026-08-19T16:00:00+00:00",
        idempotency_key="backup:test:v1",
        entries=(
            SnapshotEntry("artifact:1", "source:1", "source:1:v1", "code", HASH_A),
            SnapshotEntry("artifact:1", "source:2", "source:2:v1", "research", HASH_B),
        ),
    )
    assert "checkpoint cannot contain duplicate artifact_ref values" in validate_checkpoint(duplicate)


def test_valid_backup_receipt_matches_exact_manifest_entry_version_and_digest():
    assert validate_backup_receipt(receipt()) == []
    assert receipt_covers_manifest_entry(receipt(), manifest()) is True


def test_receipt_digest_mismatch_does_not_prove_backup():
    assert receipt_covers_manifest_entry(receipt(digest=HASH_B), manifest(digest=HASH_A)) is False


def test_stale_receipt_version_does_not_prove_fresh_backup_even_when_digest_matches():
    stale = receipt(digest=HASH_A, source_version_ref=VERSION_A)
    current = manifest(digest=HASH_A, source_version_ref=VERSION_B)
    assert receipt_covers_manifest_entry(stale, current) is False


def test_receipt_requires_timezone_aware_storage_time():
    errors = validate_backup_receipt(receipt(stored_at="2026-08-19T19:44:00"))
    assert "stored_at must include a timezone offset" in errors


def test_receipt_rejects_ambiguous_backend_metadata():
    malformed = BackupReceipt(
        checkpoint_id="checkpoint:nexus:command-center",
        artifact_ref="notion:command-center",
        backend=" google_drive ",
        stored_artifact_ref="drive:file:example-backup-doc",
        stored_at="2026-08-19T19:44:00+03:30",
        source_version_ref=VERSION_A,
        source_content_sha256=HASH_A,
    )
    assert "backend cannot have leading or trailing whitespace" in validate_backup_receipt(malformed)


def test_receipt_cannot_precede_checkpoint_capture():
    assert receipt_covers_manifest_entry(
        receipt(stored_at="2026-08-19T15:59:59+00:00"),
        manifest(captured_at="2026-08-19T16:00:00+00:00"),
    ) is False


def test_valid_restore_proof_reconstructs_exact_manifest_entry():
    proof = restore_proof()
    assert validate_restore_proof(proof) == []
    assert restore_proves_reconstruction(proof, receipt(), manifest()) is True


def test_restore_digest_mismatch_fails_closed():
    proof = restore_proof(restored_digest=HASH_B)
    assert restore_proves_reconstruction(proof, receipt(), manifest()) is False


def test_restore_expected_digest_cannot_drift_from_receipt():
    proof = restore_proof(expected_digest=HASH_B, restored_digest=HASH_B)
    assert restore_proves_reconstruction(proof, receipt(digest=HASH_A), manifest(digest=HASH_A)) is False


def test_restore_source_version_must_match_exact_receipt_version():
    proof = restore_proof(source_version_ref=VERSION_B)
    assert restore_proves_reconstruction(proof, receipt(source_version_ref=VERSION_A), manifest(source_version_ref=VERSION_A)) is False


def test_restore_backend_and_stored_ref_are_bound_to_receipt():
    assert restore_proves_reconstruction(
        restore_proof(backend="other_backend"), receipt(), manifest()
    ) is False
    assert restore_proves_reconstruction(
        restore_proof(stored_artifact_ref="drive:file:different"), receipt(), manifest()
    ) is False


def test_restore_requires_timezone_aware_timestamp():
    errors = validate_restore_proof(restore_proof(restored_at="2026-08-19T20:00:00"))
    assert "restored_at must include a timezone offset" in errors


def test_restore_rejects_ambiguous_restored_artifact_ref():
    malformed = RestoreProof(
        checkpoint_id="checkpoint:nexus:command-center",
        artifact_ref="notion:command-center",
        backend="google_drive",
        stored_artifact_ref="drive:file:example-backup-doc",
        restored_artifact_ref=" restore:test ",
        restored_at="2026-08-19T20:00:00+03:30",
        source_version_ref=VERSION_A,
        expected_content_sha256=HASH_A,
        restored_content_sha256=HASH_A,
    )
    assert "restored_artifact_ref cannot have leading or trailing whitespace" in validate_restore_proof(malformed)


def test_restore_cannot_precede_storage_write():
    assert restore_proves_reconstruction(
        restore_proof(restored_at="2026-08-19T19:43:59+03:30"),
        receipt(stored_at="2026-08-19T19:44:00+03:30"),
        manifest(),
    ) is False


@given(st.integers(min_value=1, max_value=86_400))
def test_any_receipt_timestamp_before_capture_fails_closed(seconds_before):
    captured = datetime(2026, 8, 19, 16, 0, tzinfo=timezone.utc)
    stored = captured - timedelta(seconds=seconds_before)
    assert receipt_covers_manifest_entry(
        receipt(stored_at=stored.isoformat()),
        manifest(captured_at=captured.isoformat()),
    ) is False


@given(st.integers(min_value=1, max_value=86_400))
def test_any_restore_timestamp_before_storage_fails_closed(seconds_before):
    stored = datetime(2026, 8, 19, 16, 14, tzinfo=timezone.utc)
    restored = stored - timedelta(seconds=seconds_before)
    assert restore_proves_reconstruction(
        restore_proof(restored_at=restored.isoformat()),
        receipt(stored_at=stored.isoformat()),
        manifest(captured_at="2026-08-19T16:00:00+00:00"),
    ) is False
