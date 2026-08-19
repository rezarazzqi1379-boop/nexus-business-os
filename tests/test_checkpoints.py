from datetime import datetime, timedelta, timezone

from hypothesis import given, strategies as st

from nexus_core.checkpoints import BackupReceipt, CheckpointManifest, RestoreProof, SnapshotEntry, changed_artifact_refs, checkpoint_matches, receipt_covers_manifest_entry, restore_proves_reconstruction, validate_backup_receipt, validate_checkpoint, validate_restore_proof

HASH_A = "a" * 64
HASH_B = "b" * 64
VERSION_A = "notion:page:command-center:version:1"
VERSION_B = "notion:page:command-center:version:2"


def manifest(*, digest: str = HASH_A, captured_at: str = "2026-08-19T16:00:00+00:00", source_version_ref: str = VERSION_A):
    return CheckpointManifest("checkpoint:nexus:command-center", "nexus-command-center", captured_at, "backup:nexus-command-center:v1", (SnapshotEntry("notion:command-center", "notion:page:command-center", source_version_ref, "documentation", digest),))


def receipt(*, digest: str = HASH_A, stored_at: str = "2026-08-19T19:44:00+03:30", source_version_ref: str = VERSION_A):
    return BackupReceipt("checkpoint:nexus:command-center", "notion:command-center", "google_drive", "drive:file:example-backup-doc", stored_at, source_version_ref, digest)


def restore_proof(*, expected_digest: str = HASH_A, restored_digest: str = HASH_A, restored_at: str = "2026-08-19T20:00:00+03:30", source_version_ref: str = VERSION_A, backend: str = "google_drive", stored_artifact_ref: str = "drive:file:example-backup-doc"):
    return RestoreProof("checkpoint:nexus:command-center", "notion:command-center", backend, stored_artifact_ref, "restore:test:command-center", restored_at, source_version_ref, expected_digest, restored_digest)


def test_valid_checkpoint_manifest_passes(): assert validate_checkpoint(manifest()) == []
def test_checkpoint_requires_timezone_aware_capture_time(): assert "captured_at must include a timezone offset" in validate_checkpoint(manifest(captured_at="2026-08-19T16:00:00"))
def test_invalid_digest_fails_closed(): assert "content_sha256 must be a lowercase 64-character SHA-256 hex digest" in validate_checkpoint(manifest(digest="not-a-digest"))
def test_source_version_ref_is_required(): assert "source_version_ref is required" in validate_checkpoint(manifest(source_version_ref=""))
def test_same_idempotency_key_same_source_version_and_same_content_is_a_match(): assert checkpoint_matches(manifest(captured_at="2026-08-19T17:00:00+00:00"), manifest()) is True
def test_changed_content_is_detected_for_incremental_backup(): assert changed_artifact_refs(manifest(digest=HASH_B), manifest(digest=HASH_A)) == ("notion:command-center",)
def test_valid_no_change_is_distinct_from_invalid_current_manifest():
    previous = manifest(captured_at="2026-08-19T15:00:00+00:00")
    assert changed_artifact_refs(manifest(), previous) == ()
    assert changed_artifact_refs(manifest(digest="invalid"), previous) is None

def test_invalid_previous_manifest_forces_conservative_rebackup(): assert changed_artifact_refs(manifest(), manifest(digest="invalid")) == ("notion:command-center",)
def test_new_source_version_is_changed_even_when_digest_is_identical():
    first = manifest(digest=HASH_A, source_version_ref=VERSION_A); second = manifest(digest=HASH_A, source_version_ref=VERSION_B)
    assert checkpoint_matches(second, first) is False
    assert changed_artifact_refs(second, first) == ("notion:command-center",)
def test_duplicate_artifact_refs_are_rejected():
    duplicate = CheckpointManifest("checkpoint:test", "test", "2026-08-19T16:00:00+00:00", "backup:test:v1", (SnapshotEntry("artifact:1", "source:1", "source:1:v1", "code", HASH_A), SnapshotEntry("artifact:1", "source:2", "source:2:v1", "research", HASH_B)))
    assert "checkpoint cannot contain duplicate artifact_ref values" in validate_checkpoint(duplicate)
def test_valid_backup_receipt_matches_exact_manifest_entry_version_and_digest():
    assert validate_backup_receipt(receipt()) == []
    assert receipt_covers_manifest_entry(receipt(), manifest()) is True
def test_receipt_digest_mismatch_does_not_prove_backup(): assert receipt_covers_manifest_entry(receipt(digest=HASH_B), manifest(digest=HASH_A)) is False
def test_stale_receipt_version_does_not_prove_fresh_backup_even_when_digest_matches(): assert receipt_covers_manifest_entry(receipt(source_version_ref=VERSION_A), manifest(source_version_ref=VERSION_B)) is False
def test_receipt_requires_timezone_aware_storage_time(): assert "stored_at must include a timezone offset" in validate_backup_receipt(receipt(stored_at="2026-08-19T19:44:00"))
def test_receipt_rejects_ambiguous_backend_metadata():
    malformed = BackupReceipt("checkpoint:nexus:command-center", "notion:command-center", " google_drive ", "drive:file:example-backup-doc", "2026-08-19T19:44:00+03:30", VERSION_A, HASH_A)
    assert "backend cannot have leading or trailing whitespace" in validate_backup_receipt(malformed)
def test_receipt_cannot_precede_checkpoint_capture(): assert receipt_covers_manifest_entry(receipt(stored_at="2026-08-19T15:59:59+00:00"), manifest(captured_at="2026-08-19T16:00:00+00:00")) is False
def test_valid_restore_proof_reconstructs_exact_manifest_entry():
    proof = restore_proof(); assert validate_restore_proof(proof) == []; assert restore_proves_reconstruction(proof, receipt(), manifest()) is True
def test_restore_digest_mismatch_fails_closed(): assert restore_proves_reconstruction(restore_proof(restored_digest=HASH_B), receipt(), manifest()) is False
def test_restore_expected_digest_cannot_drift_from_receipt(): assert restore_proves_reconstruction(restore_proof(expected_digest=HASH_B, restored_digest=HASH_B), receipt(), manifest()) is False
def test_restore_source_version_must_match_exact_receipt_version(): assert restore_proves_reconstruction(restore_proof(source_version_ref=VERSION_B), receipt(source_version_ref=VERSION_A), manifest(source_version_ref=VERSION_A)) is False
def test_restore_backend_and_stored_ref_are_bound_to_receipt():
    assert restore_proves_reconstruction(restore_proof(backend="other_backend"), receipt(), manifest()) is False
    assert restore_proves_reconstruction(restore_proof(stored_artifact_ref="drive:file:different"), receipt(), manifest()) is False
def test_restore_requires_timezone_aware_timestamp(): assert "restored_at must include a timezone offset" in validate_restore_proof(restore_proof(restored_at="2026-08-19T20:00:00"))
def test_restore_cannot_precede_storage_write(): assert restore_proves_reconstruction(restore_proof(restored_at="2026-08-19T19:43:59+03:30"), receipt(stored_at="2026-08-19T19:44:00+03:30"), manifest()) is False

@given(st.integers(min_value=1, max_value=86_400))
def test_any_receipt_timestamp_before_capture_fails_closed(seconds_before):
    captured = datetime(2026, 8, 19, 16, 0, tzinfo=timezone.utc); stored = captured - timedelta(seconds=seconds_before)
    assert receipt_covers_manifest_entry(receipt(stored_at=stored.isoformat()), manifest(captured_at=captured.isoformat())) is False

@given(st.integers(min_value=1, max_value=86_400))
def test_any_restore_timestamp_before_storage_fails_closed(seconds_before):
    stored = datetime(2026, 8, 19, 16, 14, tzinfo=timezone.utc); restored = stored - timedelta(seconds=seconds_before)
    assert restore_proves_reconstruction(restore_proof(restored_at=restored.isoformat()), receipt(stored_at=stored.isoformat()), manifest(captured_at="2026-08-19T16:00:00+00:00")) is False
