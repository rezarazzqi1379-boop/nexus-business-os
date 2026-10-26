"""Fail-closed, side-effect-free admission of an explicitly approved authority tuple.

This module never infers authority from document title, highest version, or file presence.
It is an independent guard; callers must wire it into consequential source selection.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping
import re

_HEX64 = re.compile(r"[0-9a-f]{64}\Z")
_VERSION = re.compile(r"v[0-9]+(?:\.[0-9]+)+\Z")


class AuthorityBlocked(ValueError):
    """The requested authority tuple has not passed admission."""


@dataclass(frozen=True)
class AuthorityBinding:
    registry_version: str
    registry_sha256: str
    master_version: str
    master_sha256: str
    approval_id: str
    approved_by: str
    evidence_ref: str


def _check_version(value: str) -> bool:
    return bool(_VERSION.fullmatch(value))


def _check_hash(value: str) -> bool:
    return bool(_HEX64.fullmatch(value))


def admit_authority(
    binding: AuthorityBinding | None,
    *,
    registry_bytes: bytes,
    master_bytes: bytes,
    approval_records: Mapping[str, AuthorityBinding],
    contradictory: bool = False,
) -> AuthorityBinding:
    """Admit only an exact, externally recorded, digest-bound human approval.

    approval_records must be populated by a separately authenticated approval
    store; this function does not verify identity, document semantics or signatures.
    """
    if binding is None or contradictory:
        raise AuthorityBlocked("authority_missing_or_contradictory")
    if not all((
        _check_version(binding.registry_version),
        _check_version(binding.master_version),
        _check_hash(binding.registry_sha256),
        _check_hash(binding.master_sha256),
        binding.approval_id.strip(),
        binding.approved_by.strip(),
        binding.evidence_ref.strip(),
    )):
        raise AuthorityBlocked("authority_binding_incomplete")
    if approval_records.get(binding.approval_id) != binding:
        raise AuthorityBlocked("authority_approval_unverified")
    if sha256(registry_bytes).hexdigest() != binding.registry_sha256:
        raise AuthorityBlocked("authority_registry_digest_mismatch")
    if sha256(master_bytes).hexdigest() != binding.master_sha256:
        raise AuthorityBlocked("authority_master_digest_mismatch")
    return binding
