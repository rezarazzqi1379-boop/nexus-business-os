"""Fail-closed, side-effect-free admission of an explicitly approved authority tuple.

This module never infers authority from document title, highest version, or file presence.
It is an independent guard; callers must wire it into consequential source selection.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Mapping
from io import BytesIO
from zipfile import ZipFile
from xml.etree import ElementTree
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


def _docx_text(raw: bytes) -> str:
    """Extract bounded paragraph text; malformed/unreadable documents block admission."""
    if len(raw) > 20 * 1024 * 1024:
        raise AuthorityBlocked("authority_document_too_large")
    try:
        with ZipFile(BytesIO(raw)) as archive:
            info = archive.getinfo("word/document.xml")
            if info.file_size > 10 * 1024 * 1024 or info.file_size / max(info.compress_size, 1) > 100:
                raise AuthorityBlocked("authority_document_expansion_rejected")
            xml = archive.read(info)
        root = ElementTree.fromstring(xml)
    except (OSError, KeyError, ValueError, ElementTree.ParseError) as exc:
        raise AuthorityBlocked("authority_document_unreadable") from exc
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    return "\n".join(
        "".join(t.text or "" for t in paragraph.iter(ns + "t"))
        for paragraph in root.iter(ns + "p")
    )


def assert_consistent_authority_declarations(registry_bytes: bytes, master_bytes: bytes,
                                             binding: AuthorityBinding) -> None:
    """Reject conflicting explicit active/governing pairs in bounded DOCX text.

    This is a conservative guard, not a substitute for human provenance review.
    """
    registry_text = _docx_text(registry_bytes)
    master_text = _docx_text(master_bytes)
    for text in (registry_text, master_text):
        for sentence in re.split(r"[.\n;]+", text):
            if not re.search(r"\b(?:active|governing|governs|canonical|authoritative)\b", sentence, re.I):
                continue
            registry_versions = re.findall(
                r"(?:source\s+registry|registry)\s*(v\d+(?:\.\d+)+)", sentence, re.I)
            master_versions = re.findall(
                r"(?:master\s+context|master)\s*(v\d+(?:\.\d+)+)", sentence, re.I)
            if any(v.casefold() != binding.registry_version.casefold() for v in registry_versions):
                raise AuthorityBlocked("authority_registry_declaration_conflict")
            if any(v.casefold() != binding.master_version.casefold() for v in master_versions):
                raise AuthorityBlocked("authority_master_declaration_conflict")
