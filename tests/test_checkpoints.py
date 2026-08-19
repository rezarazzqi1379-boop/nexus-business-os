from nexus_core.checkpoints import (
    CheckpointManifest,
    SnapshotEntry,
    changed_artifact_refs,
    checkpoint_matches,
    validate_checkpoint,
)


HASH_A = "a" * 64
HASH_B = "b" * 64


def manifest(*, digest: str = HASH_A, captured_at: str = "2026-08-19T16:00:00+00:00"):
    return CheckpointManifest(
        checkpoint_id="checkpoint:nexus:command-center",
        scope="nexus-command-center",
        captured_at=captured_at,
        idempotency_key="backup:nexus-command-center:v1",
        entries=(
            SnapshotEntry(
                artifact_ref="notion:command-center",
                source_ref="notion:page:command-center",
                category="documentation",
                content_sha256=digest,
            ),
        ),
    )


def test_valid_checkpoint_manifest_passes():
    assert validate_checkpoint(manifest()) == []


def test_checkpoint_requires_timezone_aware_capture_time():
    errors = validate_checkpoint(manifest(captured_at="2026-08-19T16:00:00"))
    assert "captured_at must include a timezone offset" in errors


def test_invalid_digest_fails_closed():
    errors = validate_checkpoint(manifest(digest="not-a-digest"))
    assert "content_sha256 must be a lowercase 64-character SHA-256 hex digest" in errors


def test_same_idempotency_key_and_same_content_is_a_match():
    first = manifest()
    second = manifest(captured_at="2026-08-19T17:00:00+00:00")
    assert checkpoint_matches(second, first) is True


def test_changed_content_is_detected_for_incremental_backup():
    first = manifest(digest=HASH_A)
    second = manifest(digest=HASH_B)
    assert checkpoint_matches(second, first) is False
    assert changed_artifact_refs(second, first) == ("notion:command-center",)


def test_duplicate_artifact_refs_are_rejected():
    duplicate = CheckpointManifest(
        checkpoint_id="checkpoint:test",
        scope="test",
        captured_at="2026-08-19T16:00:00+00:00",
        idempotency_key="backup:test:v1",
        entries=(
            SnapshotEntry("artifact:1", "source:1", "code", HASH_A),
            SnapshotEntry("artifact:1", "source:2", "research", HASH_B),
        ),
    )
    assert "checkpoint cannot contain duplicate artifact_ref values" in validate_checkpoint(duplicate)
