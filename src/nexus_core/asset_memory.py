from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Iterable

AssetSource = Literal["file_library", "chat_attachment", "generated_artifact", "google_drive", "gmail_attachment", "notion_attachment", "github_asset"]
AssetKind = Literal["document", "pdf", "spreadsheet", "image", "video", "audio", "archive", "code", "other"]
AnalysisState = Literal["unseen", "queued", "analyzed", "stale", "blocked"]
Sensitivity = Literal["public", "internal", "commercial_confidential", "personal_sensitive", "credential_secret"]

_ALLOWED_SOURCES = {"file_library", "chat_attachment", "generated_artifact", "google_drive", "gmail_attachment", "notion_attachment", "github_asset"}
_ALLOWED_KINDS = {"document", "pdf", "spreadsheet", "image", "video", "audio", "archive", "code", "other"}
_ALLOWED_ANALYSIS = {"unseen", "queued", "analyzed", "stale", "blocked"}
_ALLOWED_SENSITIVITY = {"public", "internal", "commercial_confidential", "personal_sensitive", "credential_secret"}


@dataclass(frozen=True)
class AssetRecord:
    asset_id: str
    file_name: str
    source: AssetSource
    kind: AssetKind
    stable_ref: str
    source_version_ref: str
    observed_at: datetime
    project_refs: tuple[str, ...]
    goal_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    sensitivity: Sensitivity = "internal"
    analysis_state: AnalysisState = "unseen"
    content_sha256: str | None = None
    supersedes: tuple[str, ...] = ()


@dataclass(frozen=True)
class AssetCatalog:
    assets: tuple[AssetRecord, ...]
    duplicate_groups: tuple[tuple[str, ...], ...]


def validate_asset(asset: AssetRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if not isinstance(asset, AssetRecord):
        return ("asset_must_be_asset_record",)
    for name, value in (("asset_id", asset.asset_id), ("file_name", asset.file_name), ("stable_ref", asset.stable_ref), ("source_version_ref", asset.source_version_ref)):
        if not isinstance(value, str) or not value.strip():
            errors.append(f"invalid_{name}")
    if asset.source not in _ALLOWED_SOURCES:
        errors.append("unsupported_source")
    if asset.kind not in _ALLOWED_KINDS:
        errors.append("unsupported_kind")
    if asset.analysis_state not in _ALLOWED_ANALYSIS:
        errors.append("unsupported_analysis_state")
    if asset.sensitivity not in _ALLOWED_SENSITIVITY:
        errors.append("unsupported_sensitivity")
    if asset.observed_at.tzinfo is None:
        errors.append("timezone_naive_observed_at")
    for name, refs in (("project_refs", asset.project_refs), ("goal_refs", asset.goal_refs), ("evidence_refs", asset.evidence_refs), ("supersedes", asset.supersedes)):
        if not isinstance(refs, tuple):
            errors.append(f"invalid_{name}_type")
            continue
        if len(refs) != len(set(refs)):
            errors.append(f"duplicate_{name}")
        if any(not isinstance(ref, str) or not ref.strip() for ref in refs):
            errors.append(f"invalid_{name}")
    if not asset.evidence_refs:
        errors.append("missing_evidence_refs")
    if asset.content_sha256 is not None:
        if not isinstance(asset.content_sha256, str) or len(asset.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in asset.content_sha256.lower()):
            errors.append("invalid_content_sha256")
    return tuple(errors)


def build_asset_catalog(assets: Iterable[AssetRecord]) -> AssetCatalog:
    items = tuple(assets)
    seen_ids: set[str] = set()
    by_hash: dict[str, list[str]] = {}
    by_ref: dict[tuple[str, str], list[str]] = {}
    for asset in items:
        errors = validate_asset(asset)
        if errors:
            raise ValueError(",".join(errors))
        if asset.asset_id in seen_ids:
            raise ValueError("duplicate_asset_id")
        seen_ids.add(asset.asset_id)
        if asset.content_sha256:
            by_hash.setdefault(asset.content_sha256.lower(), []).append(asset.asset_id)
        by_ref.setdefault((asset.stable_ref, asset.source_version_ref), []).append(asset.asset_id)
    groups = [tuple(ids) for ids in by_hash.values() if len(ids) > 1]
    groups.extend(tuple(ids) for ids in by_ref.values() if len(ids) > 1 and tuple(ids) not in groups)
    return AssetCatalog(items, tuple(groups))


def retainable_for_long_term(asset: AssetRecord) -> bool:
    if validate_asset(asset):
        return False
    if asset.sensitivity == "credential_secret":
        return False
    return bool(asset.project_refs or asset.goal_refs)
