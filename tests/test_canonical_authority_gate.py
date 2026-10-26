"""Regression tests for canonical store's authority admission boundary."""
import hashlib
from dataclasses import replace
from io import BytesIO
from zipfile import ZipFile

import pytest

from authority_admission import AuthorityBinding, AuthorityBlocked
from canonical_sources import CanonicalStore


def docx(text):
    buffer = BytesIO()
    with ZipFile(buffer, "w") as z:
        z.writestr("word/document.xml", '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>' + text + '</w:t></w:r></w:p></w:body></w:document>')
    return buffer.getvalue()



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
    registry_bytes, master_bytes = docx("Registry v1.8 governing"), docx("Master Context v2.1 governing")
    binding = AuthorityBinding(
        "v1.8", hashlib.sha256(registry_bytes).hexdigest(),
        "v2.1", hashlib.sha256(master_bytes).hexdigest(),
        "approved-001", "human", "evidence/approved-001",
    )
    with pytest.raises(AuthorityBlocked, match="authority_store_tuple_mismatch"):
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


def test_approved_historical_tuple_is_not_rejected_for_newer_version(tmp_path):
    store = CanonicalStore(tmp_path / "sources.db")
    registry_bytes, master_bytes = docx("Registry v1.1 governing"), docx("Master Context v1.4 governing")
    registry_digest = hashlib.sha256(registry_bytes).hexdigest()
    master_digest = hashlib.sha256(master_bytes).hexdigest()
    with store._connect() as db:
        for source_id, version, digest in (
            ("NEXUS-SOURCE-REGISTRY", "v1.1", registry_digest),
            ("NEXUS-MASTER-CONTEXT", "v1.4", master_digest),
            ("NEXUS-SOURCE-REGISTRY", "v1.8", "a" * 64),
            ("NEXUS-MASTER-CONTEXT", "v2.1", "b" * 64),
        ):
            db.execute(
                "INSERT INTO canonical_source_versions "
                "(source_id,version_key,project_id,title,version,status,effective_date,sha256,content,ingested_at) "
                "VALUES (?,?,?,?,?,?,?,?,?,?)",
                (source_id, version, None, source_id, version, "UNVERIFIED", None,
                 digest, "historical fixture", "2026-10-26T00:00:00Z"),
            )
    approved = AuthorityBinding(
        "v1.1", registry_digest, "v1.4", master_digest,
        "approved-historical", "human", "evidence/historical",
    )
    assert store.admit_active_tuple(
        approved, registry_bytes=registry_bytes, master_bytes=master_bytes,
        approval_records={approved.approval_id: approved},
    ) == approved
    assert not any(row["active"] for row in store.status()["sources"])
