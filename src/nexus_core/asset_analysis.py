from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Iterable

from .asset_memory import AssetRecord, validate_asset

AnalysisRoute = Literal["text_extract", "pdf_structure", "spreadsheet_profile", "vision_analysis", "video_review", "audio_review", "code_analysis", "archive_inventory", "generic_metadata"]


@dataclass(frozen=True)
class AnalysisTask:
    task_id: str
    asset_id: str
    route: AnalysisRoute
    priority: int
    reason: str
    source_version_ref: str


@dataclass(frozen=True)
class AnalysisResult:
    asset_id: str
    source_version_ref: str
    summary_ref: str
    finding_refs: tuple[str, ...]
    derived_asset_refs: tuple[str, ...] = ()


def analysis_route(asset: AssetRecord) -> AnalysisRoute:
    if asset.kind == "pdf": return "pdf_structure"
    if asset.kind == "spreadsheet": return "spreadsheet_profile"
    if asset.kind == "image": return "vision_analysis"
    if asset.kind == "video": return "video_review"
    if asset.kind == "audio": return "audio_review"
    if asset.kind == "code": return "code_analysis"
    if asset.kind == "archive": return "archive_inventory"
    if asset.kind == "document": return "text_extract"
    return "generic_metadata"


def queue_asset_analysis(assets: Iterable[AssetRecord], active_project_refs: tuple[str, ...] = ()) -> tuple[AnalysisTask, ...]:
    tasks: list[AnalysisTask] = []
    seen: set[str] = set()
    active = set(active_project_refs)
    for asset in assets:
        errors = validate_asset(asset)
        if errors:
            raise ValueError(",".join(errors))
        if asset.asset_id in seen:
            raise ValueError("duplicate_asset_id")
        seen.add(asset.asset_id)
        if asset.analysis_state == "blocked" or asset.sensitivity == "credential_secret":
            continue
        if asset.analysis_state == "analyzed":
            continue
        project_match = bool(active & set(asset.project_refs))
        priority = 100 if project_match else 50
        if asset.analysis_state == "stale":
            priority += 20
        if asset.kind in {"pdf", "spreadsheet", "image"}:
            priority += 10
        tasks.append(AnalysisTask(
            task_id=f"analyze:{asset.asset_id}:{asset.source_version_ref}",
            asset_id=asset.asset_id,
            route=analysis_route(asset),
            priority=priority,
            reason="active_project" if project_match else "background_asset_memory",
            source_version_ref=asset.source_version_ref,
        ))
    tasks.sort(key=lambda t: (-t.priority, t.task_id))
    return tuple(tasks)


def validate_analysis_result(result: AnalysisResult, asset: AssetRecord) -> tuple[str, ...]:
    errors: list[str] = []
    if result.asset_id != asset.asset_id:
        errors.append("asset_identity_mismatch")
    if result.source_version_ref != asset.source_version_ref:
        errors.append("stale_analysis_result")
    if not isinstance(result.summary_ref, str) or not result.summary_ref.strip():
        errors.append("missing_summary_ref")
    if len(result.finding_refs) != len(set(result.finding_refs)):
        errors.append("duplicate_finding_refs")
    if any(not isinstance(ref, str) or not ref.strip() for ref in result.finding_refs):
        errors.append("invalid_finding_ref")
    return tuple(errors)
