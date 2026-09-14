"""NEXUS Expert Foundry v0.1: governed memory for science, experience and invention.

This module records knowledge; it does not operate equipment, change a process recipe,
promote a claim to fact, or authorize an experiment. All records remain scoped,
versioned and reviewable. Runtime coordination remains repository-backed.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import IO, Iterable

if sys.platform == "win32":
    import msvcrt
    import time

    def _acquire_lock(handle: IO[bytes]) -> None:
        handle.seek(0)
        while True:
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                return
            except OSError:
                time.sleep(0.005)

    def _release_lock(handle: IO[bytes]) -> None:
        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl

    def _acquire_lock(handle: IO[bytes]) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)

    def _release_lock(handle: IO[bytes]) -> None:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


SCHEMA_VERSION = "nexus.expert-foundry.v1"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,95}$")
RECORD_TYPES = frozenset({
    "RESEARCH_RUN", "CONVERSATION", "SOURCE", "CLAIM", "EXPERIENCE",
    "HYPOTHESIS", "EXPERIMENT", "RESULT", "INVENTION",
})
SOURCE_CLASSES = frozenset({
    "PRIMARY_RESEARCH", "STANDARD", "PATENT", "MANUFACTURER_DOCUMENTATION",
    "PLANT_MEASUREMENT", "LAB_RESULT", "EXPERT_INTERVIEW", "OPERATOR_OBSERVATION",
    "MAINTENANCE_RECORD", "FAILURE_REPORT", "SECONDARY_ANALYSIS", "ANECDOTE",
})
VERIFICATION_STATES = frozenset({
    "UNVERIFIED", "REVIEWED", "CORROBORATED", "EMPIRICALLY_SUPPORTED",
    "REJECTED", "SUPERSEDED",
})
MATURITY_STATES = frozenset({
    "CAPTURED", "STRUCTURED", "TESTED", "VALIDATED", "PROMOTED",
})
EXPERIMENT_STATES = frozenset({"DRAFT", "REVIEW_REQUIRED", "APPROVED", "RUN", "CLOSED"})
PROMOTION_DECISIONS = frozenset({"PROMOTE", "HOLD", "REJECT", "SUPERSEDE"})


def _safe_id(value: str, field: str) -> None:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid_{field}")


def _utc(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _unit_rate(value: float, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"invalid_{field}")


def _nonempty(values: Iterable[str], field: str) -> None:
    values = tuple(values)
    if not values or any(not isinstance(value, str) or not value.strip() for value in values):
        raise ValueError(f"invalid_{field}")


def _scope(project_id: str, lane_id: str | None) -> None:
    _safe_id(project_id, "project_id")
    if lane_id is not None:
        _safe_id(lane_id, "lane_id")


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class KnowledgeRecord:
    record_id: str
    record_type: str
    domain: str
    title: str
    statement: str
    source_class: str
    source_locator: str
    captured_at: str
    confidence: float
    verification_state: str = "UNVERIFIED"
    maturity_state: str = "CAPTURED"
    project_id: str = ""
    lane_id: str | None = None
    operating_context: str = ""
    applicability_limits: str = ""
    uncertainty: str = ""
    supersedes: str | None = None
    contradiction_refs: tuple[str, ...] = ()

    def validate(self) -> None:
        _safe_id(self.record_id, "record_id")
        if self.record_type not in RECORD_TYPES:
            raise ValueError("invalid_record_type")
        if self.source_class not in SOURCE_CLASSES:
            raise ValueError("invalid_source_class")
        if self.verification_state not in VERIFICATION_STATES:
            raise ValueError("invalid_verification_state")
        if self.maturity_state not in MATURITY_STATES:
            raise ValueError("invalid_maturity_state")
        _nonempty((self.domain, self.title, self.statement, self.source_locator), "knowledge_identity")
        _utc(self.captured_at, "captured_at")
        _unit_rate(self.confidence, "confidence")
        _scope(self.project_id, self.lane_id)
        if self.record_type == "EXPERIENCE" and not self.operating_context.strip():
            raise ValueError("experience_requires_operating_context")
        if self.record_type == "SOURCE" and self.verification_state != "UNVERIFIED":
            raise ValueError("raw_source_cannot_arrive_preverified")
        if self.maturity_state == "PROMOTED":
            raise ValueError("promoted_state_requires_store_transition")
        if self.supersedes is not None:
            _safe_id(self.supersedes, "supersedes")
        if len(set(self.contradiction_refs)) != len(self.contradiction_refs):
            raise ValueError("duplicate_contradiction_ref")
        for ref in self.contradiction_refs:
            _safe_id(ref, "contradiction_ref")

    @property
    def digest(self) -> str:
        self.validate()
        return sha256(_canonical_json(asdict(self)).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExperienceRecord:
    knowledge: KnowledgeRecord
    observer_role: str
    occurrence_count: int
    observed_outcome: str
    validation_plan: str
    safety_critical: bool

    def validate(self) -> None:
        self.knowledge.validate()
        if self.knowledge.record_type != "EXPERIENCE":
            raise ValueError("experience_wrapper_requires_experience_record")
        _nonempty((self.observer_role, self.observed_outcome, self.validation_plan), "experience_detail")
        if isinstance(self.occurrence_count, bool) or not isinstance(self.occurrence_count, int) or self.occurrence_count < 1:
            raise ValueError("invalid_occurrence_count")
        if not isinstance(self.safety_critical, bool):
            raise ValueError("invalid_safety_critical")

    @property
    def project_id(self) -> str:
        return self.knowledge.project_id

    @property
    def lane_id(self) -> str | None:
        return self.knowledge.lane_id


@dataclass(frozen=True)
class HypothesisRecord:
    hypothesis_id: str
    domain: str
    problem: str
    proposed_mechanism: str
    predicted_outcome: str
    falsification_test: str
    evidence_refs: tuple[str, ...]
    experience_refs: tuple[str, ...]
    alternative_hypotheses: tuple[str, ...]
    created_at: str
    project_id: str = ""
    lane_id: str | None = None
    status: str = "DRAFT"

    def validate(self) -> None:
        _safe_id(self.hypothesis_id, "hypothesis_id")
        _nonempty((self.domain, self.problem, self.proposed_mechanism,
                   self.predicted_outcome, self.falsification_test), "hypothesis")
        if not self.evidence_refs and not self.experience_refs:
            raise ValueError("hypothesis_requires_grounding")
        if not self.alternative_hypotheses:
            raise ValueError("hypothesis_requires_alternatives")
        if self.status not in EXPERIMENT_STATES:
            raise ValueError("invalid_hypothesis_status")
        for ref in self.evidence_refs + self.experience_refs:
            _safe_id(ref, "hypothesis_ref")
        _nonempty(self.alternative_hypotheses, "alternative_hypothesis")
        _utc(self.created_at, "created_at")
        _scope(self.project_id, self.lane_id)


@dataclass(frozen=True)
class ResearchTrace:
    run_id: str
    objective: str
    exact_queries: tuple[str, ...]
    provider_ids: tuple[str, ...]
    source_refs: tuple[str, ...]
    rejected_source_refs: tuple[str, ...]
    gap_refs: tuple[str, ...]
    started_at: str
    stopped_at: str
    stopping_reason: str
    project_id: str = ""
    lane_id: str | None = None
    retrieval_mode: str = "LIVE_SEARCH"

    def validate(self) -> None:
        _safe_id(self.run_id, "run_id")
        _nonempty((self.objective, self.stopping_reason), "research_trace")
        if self.retrieval_mode not in {"LIVE_SEARCH", "STATIC_CURATED"}:
            raise ValueError("invalid_retrieval_mode")
        if self.retrieval_mode == "LIVE_SEARCH" and not self.exact_queries:
            raise ValueError("research_trace_requires_query")
        if self.retrieval_mode == "STATIC_CURATED" and self.exact_queries:
            raise ValueError("static_trace_cannot_claim_queries")
        if self.exact_queries:
            _nonempty(self.exact_queries, "exact_query")
        _nonempty(self.provider_ids, "provider_id")
        for ref in self.source_refs + self.rejected_source_refs + self.gap_refs:
            _safe_id(ref, "research_trace_ref")
        started = _utc(self.started_at, "started_at")
        stopped = _utc(self.stopped_at, "stopped_at")
        if stopped < started:
            raise ValueError("research_trace_stops_before_start")
        _scope(self.project_id, self.lane_id)


@dataclass(frozen=True)
class ConversationRecord:
    conversation_id: str
    platform: str
    participant_roles: tuple[str, ...]
    source_locator: str
    captured_at: str
    extracted_record_refs: tuple[str, ...]
    content_sha256: str
    project_id: str
    lane_id: str | None = None
    authority_state: str = "UNTRUSTED_CONTEXT"

    def validate(self) -> None:
        _safe_id(self.conversation_id, "conversation_id")
        _nonempty((self.platform, self.source_locator), "conversation_identity")
        if not self.participant_roles:
            raise ValueError("conversation_requires_participants")
        _nonempty(self.participant_roles, "participant_role")
        if self.authority_state != "UNTRUSTED_CONTEXT":
            raise ValueError("conversation_cannot_be_authority")
        if not re.fullmatch(r"[0-9a-f]{64}", self.content_sha256):
            raise ValueError("invalid_content_sha256")
        _scope(self.project_id, self.lane_id)
        for ref in self.extracted_record_refs:
            _safe_id(ref, "conversation_record_ref")
        _utc(self.captured_at, "captured_at")


@dataclass(frozen=True)
class PromotionDecision:
    decision_id: str
    record_id: str
    decision: str
    reviewer: str
    evidence_refs: tuple[str, ...]
    evaluation_ref: str
    decided_at: str
    rationale: str
    project_id: str
    lane_id: str | None = None
    human_approval_id: str | None = None

    def validate(self) -> None:
        _safe_id(self.decision_id, "decision_id")
        _safe_id(self.record_id, "record_id")
        if self.decision not in PROMOTION_DECISIONS:
            raise ValueError("invalid_promotion_decision")
        _nonempty((self.reviewer, self.evaluation_ref, self.rationale), "promotion_decision")
        if self.decision == "PROMOTE":
            if not self.evidence_refs:
                raise ValueError("promotion_requires_evidence")
            if self.human_approval_id is None:
                raise ValueError("promotion_requires_human_approval")
        for ref in self.evidence_refs:
            _safe_id(ref, "promotion_evidence_ref")
        if self.human_approval_id is not None:
            _safe_id(self.human_approval_id, "human_approval_id")
        _utc(self.decided_at, "decided_at")
        _scope(self.project_id, self.lane_id)


class ExpertFoundryStore:
    """Append-only hash-chained event store with deterministic snapshot backups."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.events_path = self.root / "events.jsonl"
        self.snapshots_dir = self.root / "snapshots"
        self.lock_path = self.root / ".store.lock"
        self.root.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def _locked(self):
        """Serialize writers across threads and processes sharing this store root."""
        with self.lock_path.open("a+b") as handle:
            _acquire_lock(handle)
            try:
                yield
            finally:
                _release_lock(handle)

    def _last_hash(self) -> str:
        if not self.events_path.exists():
            return "0" * 64
        lines = [line for line in self.events_path.read_text(encoding="utf-8").splitlines() if line]
        return json.loads(lines[-1])["event_hash"] if lines else "0" * 64

    def _write_envelope_locked(self, event_type: str, payload: dict) -> str:
        """Caller must hold self._locked(). Appends one hash-chained event."""
        envelope = {
            "schema_version": SCHEMA_VERSION, "event_id": uuid.uuid4().hex,
            "event_type": event_type, "previous_hash": self._last_hash(), "payload": payload,
        }
        envelope["event_hash"] = sha256(_canonical_json(envelope).encode("utf-8")).hexdigest()
        with self.events_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(_canonical_json(envelope) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return envelope["event_hash"]

    def append(self, record: KnowledgeRecord | ExperienceRecord | HypothesisRecord | ResearchTrace |
               ConversationRecord | PromotionDecision) -> str:
        record.validate()
        payload = asdict(record)
        with self._locked():
            return self._write_envelope_locked(type(record).__name__, payload)

    def promote(self, record: KnowledgeRecord, decision: PromotionDecision) -> str:
        """Record an approved promotion; direct PROMOTED records are forbidden."""
        record.validate()
        decision.validate()
        if decision.decision != "PROMOTE" or decision.record_id != record.record_id:
            raise ValueError("promotion_decision_mismatch")
        if (decision.project_id, decision.lane_id) != (record.project_id, record.lane_id):
            raise ValueError("cross_scope_promotion")
        if record.verification_state not in {"CORROBORATED", "EMPIRICALLY_SUPPORTED"}:
            raise ValueError("promotion_requires_support")
        promoted = asdict(record)
        promoted["maturity_state"] = "PROMOTED"
        payload = {"record": promoted, "decision": asdict(decision)}
        with self._locked():
            return self._write_envelope_locked("PromotionEvent", payload)

    def verify_chain(self) -> bool:
        previous = "0" * 64
        if not self.events_path.exists():
            return True
        for line in self.events_path.read_text(encoding="utf-8").splitlines():
            envelope = json.loads(line)
            event_hash = envelope.pop("event_hash")
            if envelope["previous_hash"] != previous:
                return False
            if sha256(_canonical_json(envelope).encode("utf-8")).hexdigest() != event_hash:
                return False
            previous = event_hash
        return True

    def create_snapshot(self, snapshot_id: str) -> Path:
        _safe_id(snapshot_id, "snapshot_id")
        target = self.snapshots_dir / f"{snapshot_id}.json"
        with self._locked():
            if not self.verify_chain():
                raise ValueError("cannot_snapshot_invalid_chain")
            content = self.events_path.read_text(encoding="utf-8") if self.events_path.exists() else ""
            digest = sha256(content.encode("utf-8")).hexdigest()
            payload = {"schema_version": SCHEMA_VERSION, "snapshot_id": snapshot_id,
                       "events_sha256": digest, "events": content.splitlines()}
            try:
                descriptor = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                raise FileExistsError("snapshot_already_exists") from None
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
            except BaseException:
                target.unlink(missing_ok=True)
                raise
        return target
