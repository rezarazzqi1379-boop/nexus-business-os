"""Evidence-first ingestion of educational video transcripts and notes."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Literal
from urllib.parse import urlsplit

LicenseState = Literal["public", "licensed", "user_provided", "unknown"]


@dataclass(frozen=True)
class LearningMedia:
    media_id: str
    project_id: str
    title: str
    source_url: str
    publisher: str
    published_at: str | None
    retrieved_at: str
    license_state: LicenseState
    language: str

    def validate(self) -> None:
        if not all(x.strip() for x in (self.media_id, self.project_id, self.title, self.source_url,
                                      self.publisher, self.retrieved_at, self.language)):
            raise ValueError("invalid_learning_media")
        parsed = urlsplit(self.source_url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise ValueError("unsafe_media_url")
        if self.license_state not in {"public", "licensed", "user_provided", "unknown"}:
            raise ValueError("invalid_media_license")
        for value in (self.published_at, self.retrieved_at):
            if value:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if dt.tzinfo is None:
                    raise ValueError("media_time_requires_timezone")


@dataclass(frozen=True)
class TranscriptSegment:
    start_seconds: float
    end_seconds: float
    text: str

    def validate(self) -> None:
        if self.start_seconds < 0 or self.end_seconds <= self.start_seconds or not self.text.strip():
            raise ValueError("invalid_transcript_segment")
        if len(self.text) > 20_000:
            raise ValueError("transcript_segment_too_large")


@dataclass(frozen=True)
class LearningArtifact:
    artifact_id: str
    media_id: str
    transcript_sha256: str
    source_ref: str
    claims: tuple[str, ...]
    suspicious_segments: tuple[int, ...]
    verification_state: str
    eligible_for_skill_proposal: bool


_INJECTION_PATTERNS = (
    re.compile(r"ignore (all |the )?(previous|prior) instructions", re.I),
    re.compile(r"system prompt", re.I),
    re.compile(r"reveal (your |the )?(secret|password|token|key)", re.I),
)


def ingest_transcript(media: LearningMedia, segments: Iterable[TranscriptSegment], *, claims: Iterable[str]) -> LearningArtifact:
    """Ingest authorized transcript text; never downloads or republishes the video."""
    media.validate()
    items = tuple(segments)
    if not items or len(items) > 50_000:
        raise ValueError("invalid_transcript_size")
    previous_end = -1.0
    suspicious = []
    for index, segment in enumerate(items):
        segment.validate()
        if segment.start_seconds < previous_end:
            raise ValueError("overlapping_transcript_segments")
        previous_end = segment.end_seconds
        if any(pattern.search(segment.text) for pattern in _INJECTION_PATTERNS):
            suspicious.append(index)
    body = "\n".join(f"{s.start_seconds:.3f}-{s.end_seconds:.3f}:{s.text.strip()}" for s in items)
    digest = hashlib.sha256(body.encode()).hexdigest()
    clean_claims = tuple(dict.fromkeys(c.strip() for c in claims if c.strip()))
    artifact_id = "media_" + hashlib.sha256(f"{media.media_id}|{digest}".encode()).hexdigest()[:16]
    eligible = media.license_state != "unknown" and not suspicious and len(clean_claims) > 0
    return LearningArtifact(
        artifact_id, media.media_id, digest, f"media:{media.media_id}:{digest}", clean_claims,
        tuple(suspicious), "unverified", eligible,
    )


def learning_experiment(artifact: LearningArtifact, *, corroborating_source_refs: tuple[str, ...]) -> dict:
    refs = tuple(dict.fromkeys((artifact.source_ref, *corroborating_source_refs)))
    if not artifact.eligible_for_skill_proposal or len(refs) < 3:
        return {"decision": "WATCH", "reason": "insufficient_safe_independent_evidence", "source_refs": refs}
    return {
        "decision": "EXPERIMENT",
        "instruction": "Test the generalized procedure; do not copy media wording or treat claims as facts.",
        "source_refs": refs,
        "acceptance_tests": ("frozen_task_improves", "no_policy_regression", "no_project_contamination"),
        "auto_promote": False,
    }

