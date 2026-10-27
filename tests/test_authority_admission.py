import hashlib
from dataclasses import replace

import pytest

from authority_admission import AuthorityBinding, AuthorityBlocked, admit_authority


REGISTRY = b"registry approved bytes"
MASTER = b"master approved bytes"


def binding():
    return AuthorityBinding(
        registry_version="v1.8",
        registry_sha256=hashlib.sha256(REGISTRY).hexdigest(),
        master_version="v2.1",
        master_sha256=hashlib.sha256(MASTER).hexdigest(),
        approval_id="human-approved-tuple-001",
        approved_by="human-reviewer",
        evidence_ref="authenticated-approval-store/001",
    )


def test_exact_approved_bytes_admitted_only_without_contradiction():
    b = binding()
    assert admit_authority(b, registry_bytes=REGISTRY, master_bytes=MASTER,
                           approval_records={b.approval_id: b}) == b


@pytest.mark.parametrize("reason,record,registry,master,contradictory", [
    ("missing approval", {}, REGISTRY, MASTER, False),
    ("modified registry", None, REGISTRY + b"x", MASTER, False),
    ("modified master", None, REGISTRY, MASTER + b"x", False),
    ("contradictory declarations", None, REGISTRY, MASTER, True),
])
def test_fail_closed(reason, record, registry, master, contradictory):
    b = binding()
    records = {b.approval_id: b} if record is None else record
    with pytest.raises(AuthorityBlocked):
        admit_authority(b, registry_bytes=registry, master_bytes=master,
                        approval_records=records, contradictory=contradictory)


def test_approval_cannot_be_reused_for_a_different_tuple():
    b = binding()
    other = replace(b, master_version="v2.2")
    with pytest.raises(AuthorityBlocked, match="approval_unverified"):
        admit_authority(other, registry_bytes=REGISTRY, master_bytes=MASTER,
                        approval_records={b.approval_id: b})


def test_incomplete_provenance_rejected():
    b = replace(binding(), approved_by="")
    with pytest.raises(AuthorityBlocked, match="binding_incomplete"):
        admit_authority(b, registry_bytes=REGISTRY, master_bytes=MASTER,
                        approval_records={b.approval_id: b})


def test_missing_binding_rejected():
    with pytest.raises(AuthorityBlocked):
        admit_authority(None, registry_bytes=REGISTRY, master_bytes=MASTER,
                        approval_records={})
