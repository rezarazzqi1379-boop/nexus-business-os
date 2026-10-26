"""Regression tests for canonical store's authority admission boundary."""
import hashlib
from dataclasses import replace

import pytest

from authority_admission import AuthorityBinding, AuthorityBlocked
from canonical_sources import CanonicalStore


def test_status_never_promotes_ingested_unapproved_registry(tmp_path):
    store = CanonicalStore(tmp_path / "sources.db")
    with store._connect() as db:
        db.execute(
            "INSERT INTO canonical_source_versions "
            "(source_id,version_key,project_id,title,version,status,effective_date,sha256,content,ingested_at) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            ("NEXUS-SOURCE-REGISTRY", "v1.8", None, "NEXUS SOURCE REGISTRY v1.8",
             "v1.8", "CANONICAL", "2026-09-01", "a" * 64,
             "NEXUS SOURCE REGISTRY v1.8", "2026-10-26T00:00:00Z"),
        )
    row = store.status()["sources"][0]
    assert row["active"] is False


def test_explicit_tuple_requires_store_digest_match(tmp_path):
    store = CanonicalStore(tmp_path / "sources.db")
    registry_bytes, master_bytes = b"registry", b"master"
    binding = AuthorityBinding(
        "v1.8", hashlib.sha256(registry_bytes).hexdigest(),
        "v2.1", hashlib.sha256(master_bytes).hexdigest(),
        "approved-001", "human", "evidence/approved-001",
    )
    with pytest.raises(KeyError):
        store.admit_active_tuple(
            binding, registry_bytes=registry_bytes, master_bytes=master_bytes,
            approval_records={binding.approval_id: binding},
        )


def test_contradictory_approved_tuple_is_blocked_before_store_access(tmp_path):
    store = CanonicalStore(tmp_path / "sources.db")
    registry_bytes, master_bytes = b"registry", b"master"
    binding = AuthorityBinding(
        "v1.8", hashlib.sha256(registry_bytes).hexdigest(),
        "v2.1", hashlib.sha256(master_bytes).hexdigest(),
        "approved-001", "human", "evidence/approved-001",
    )
    with pytest.raises(AuthorityBlocked, match="contradictory"):
        store.admit_active_tuple(
            binding, registry_bytes=registry_bytes, master_bytes=master_bytes,
            approval_records={binding.approval_id: binding}, contradictory=True,
        )
