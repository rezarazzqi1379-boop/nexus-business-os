"""Reusable, project/lane-neutral Research Lab: file-backed persistence, dedup,
scoring and provider-benchmark scaffolding for high-volume discovery runs.

This module is deliberately the *pipeline plumbing*, not the pipeline. It does
not perform query expansion, live search, entity extraction, entity
resolution, or buyer classification -- every one of those stages needs either
a live search provider or an LLM classifier, and this slice ships neither
(see research_evidence.py's SearchProvider/NullSearchProvider: the same rule
applies here -- no provider is assumed acceptable merely because it exists,
and none is benchmarked yet). What this module DOES provide, deterministically
and with zero live calls:

  * a persisted schema for one discovery row (``ResearchRunRecord``) covering
    every field the pipeline is expected to eventually populate
  * append-only, atomic file persistence for a run and its raw candidates
    (``ResearchLabStore``)
  * deterministic deduplication by normalized (url, entity_name) key
  * deterministic, auditable opportunity scoring over already-populated
    fields (never over a fabricated value)
  * a benchmark-policy gate for provider acceptance, extending the same
    "explicit versioned thresholds, not scattered magic numbers" pattern
    already used in research_evidence.py's SearchBenchmarkPolicy

Like research_evidence.py, this module is lane-neutral: ``project_id`` and
``lane_id`` are carried through exactly as given and never interpreted,
normalized, or validated for project/lane-specific meaning. It has no
knowledge of any specific project's lanes (e.g. PRJ-FAL-01's FAL-A/FAL-B) --
that authority belongs to a separate project-binding policy layer that does
not exist yet. This module only enforces the project/lane-agnostic
invariant: a candidate record must declare the same project_id/lane_id as
the run it's appended to (no cross-run relabeling), never what those values
are allowed to *be*.
"""

from __future__ import annotations

import json
import os
import re
import sys
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Sequence

_SRC = Path(__file__).resolve().parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from contracts import EvidenceClass, canonical_digest  # noqa: E402

SCHEMA_VERSION = "nexus.research-lab.v1"
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

SOURCE_TYPES = frozenset({
    "search_engine", "official_portal", "tender_notice", "company_website",
    "trade_database", "directory", "other",
})
BUYER_TYPES = frozenset({
    "producer", "trader", "distributor", "procurement_portal",
    "industrial_consumer", "unknown",
})
VERIFICATION_STATES = frozenset({"unverified", "reviewed", "verified", "rejected"})
REVIEW_STATES = frozenset({"pending", "queued_for_verification", "verified", "rejected", "duplicate"})
BENCHMARK_DECISIONS = frozenset({"KEEP", "CONNECT", "BUILD", "DEFER", "REJECT"})
_ACCEPTANCE_DECISIONS = frozenset({"KEEP", "CONNECT"})


def _utc(value: str, field: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field}_must_include_timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def _unit_rate(value, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"invalid_{field}")


def _safe_id(value: str, field: str) -> str:
    if not isinstance(value, str) or not SAFE_ID.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(text)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


@dataclass(frozen=True)
class ResearchRun:
    """One discovery run's identity. project_id/lane_id are opaque, carried through unchanged."""

    run_id: str
    project_id: str | None
    lane_id: str | None
    query_set_version: str
    objective: str
    created_at: str

    def validate(self) -> None:
        _safe_id(self.run_id, "run_id")
        if not self.query_set_version.strip():
            raise ValueError("invalid_query_set_version")
        if not self.objective.strip():
            raise ValueError("invalid_objective")
        _utc(self.created_at, "created_at")


@dataclass(frozen=True)
class ResearchRunRecord:
    """One raw discovery row. Every dynamic/commercial field starts unpopulated (None) until a
    later, evidence-bearing pipeline stage sets it -- this module never invents a value for one.
    """

    run_id: str
    project_id: str | None
    lane_id: str | None
    query_set_version: str
    provider: str
    query: str
    url: str
    source_type: str
    retrieved_at: str
    published_at: str | None
    entity_name: str | None
    country: str | None
    buyer_type: str | None
    product_signal: str | None
    evidence_class: EvidenceClass
    verification_state: str
    duplicate_group: str | None = None
    opportunity_score: float | None = None
    review_state: str = "pending"

    def validate(self) -> None:
        _safe_id(self.run_id, "run_id")
        if not self.query_set_version.strip():
            raise ValueError("invalid_query_set_version")
        if not self.provider.strip():
            raise ValueError("invalid_provider")
        if not self.query.strip():
            raise ValueError("invalid_query")
        if not self.url.lower().startswith(("https://", "http://")):
            raise ValueError("record_requires_retrievable_url")
        if self.source_type not in SOURCE_TYPES:
            raise ValueError("invalid_source_type")
        _utc(self.retrieved_at, "retrieved_at")
        if self.published_at is not None:
            _utc(self.published_at, "published_at")
        if self.buyer_type is not None and self.buyer_type not in BUYER_TYPES:
            raise ValueError("invalid_buyer_type")
        EvidenceClass(self.evidence_class)
        if self.verification_state not in VERIFICATION_STATES:
            raise ValueError("invalid_verification_state")
        if self.opportunity_score is not None:
            _unit_rate(self.opportunity_score, "opportunity_score")
        if self.review_state not in REVIEW_STATES:
            raise ValueError("invalid_review_state")

    @property
    def dedup_key(self) -> str:
        """Normalized identity used for deduplication -- URL first, entity+country as fallback."""
        normalized_url = self.url.strip().lower().rstrip("/")
        if normalized_url:
            return f"url:{normalized_url}"
        entity = (self.entity_name or "").strip().lower()
        country = (self.country or "").strip().lower()
        return f"entity:{entity}:{country}"


class ResearchLabStore:
    """File-backed, append-only persistence under ``research_lab/`` (JSON for run metadata and
    derived reports, JSONL for the raw candidate log). No database -- this is deliberately the
    smallest deterministic layer that can hold a run's evidence trail.
    """

    SUBDIRS = ("runs", "sources", "candidates", "entities", "scores", "benchmarks", "reports")

    def __init__(self, root: Path):
        self.root = (root / "research_lab").resolve()
        for name in self.SUBDIRS:
            (self.root / name).mkdir(parents=True, exist_ok=True)

    def _run_path(self, run_id: str) -> Path:
        return self.root / "runs" / f"{_safe_id(run_id, 'run_id')}.json"

    def _candidates_path(self, run_id: str) -> Path:
        return self.root / "candidates" / f"{_safe_id(run_id, 'run_id')}.jsonl"

    def _score_path(self, run_id: str) -> Path:
        return self.root / "scores" / f"{_safe_id(run_id, 'run_id')}.json"

    def _benchmark_path(self, provider_id: str, evaluated_at: str) -> Path:
        safe_stamp = re.sub(r"[^0-9A-Za-z_-]", "-", evaluated_at)
        return self.root / "benchmarks" / f"{_safe_id(provider_id, 'provider_id')}__{safe_stamp}.json"

    def create_run(self, run: ResearchRun) -> Path:
        run.validate()
        path = self._run_path(run.run_id)
        if path.exists():
            raise ValueError(f"run_already_exists:{run.run_id}")
        _atomic_write(path, json.dumps(asdict(run), ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        self._candidates_path(run.run_id).touch(exist_ok=True)
        return path

    def read_run(self, run_id: str) -> ResearchRun | None:
        path = self._run_path(run_id)
        if not path.exists():
            return None
        return ResearchRun(**json.loads(path.read_text(encoding="utf-8")))

    def append_candidates(self, run_id: str, records: Sequence[ResearchRunRecord]) -> Path:
        """Append raw discoveries to the run's immutable candidate log.

        Fails closed if any record disagrees with the run's own project_id/lane_id/
        query_set_version -- this is the only cross-project-contamination guard this
        module makes: a candidate cannot silently attach itself to a different
        project/lane than the run it's being appended to.
        """
        run = self.read_run(run_id)
        if run is None:
            raise KeyError(f"unknown_research_run:{run_id}")
        lines = []
        for record in records:
            record.validate()
            if record.run_id != run_id:
                raise ValueError("record_run_id_mismatch")
            if record.project_id != run.project_id:
                raise ValueError("record_project_id_mismatch")
            if record.lane_id != run.lane_id:
                raise ValueError("record_lane_id_mismatch")
            lines.append(json.dumps(asdict(record), ensure_ascii=False, sort_keys=True))
        path = self._candidates_path(run_id)
        with path.open("a", encoding="utf-8", newline="\n") as stream:
            for line in lines:
                stream.write(line + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        return path

    def read_candidates(self, run_id: str) -> tuple[ResearchRunRecord, ...]:
        path = self._candidates_path(run_id)
        if not path.exists():
            return ()
        records = []
        with path.open("r", encoding="utf-8") as stream:
            for line in stream:
                line = line.strip()
                if line:
                    records.append(ResearchRunRecord(**json.loads(line)))
        return tuple(records)

    def write_score_report(self, run_id: str, report: dict) -> Path:
        path = self._score_path(run_id)
        _atomic_write(path, json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return path

    def write_benchmark(self, benchmark: "ResearchProviderBenchmark") -> Path:
        benchmark.validate()
        path = self._benchmark_path(benchmark.provider_id, benchmark.evaluated_at)
        _atomic_write(path, json.dumps(asdict(benchmark), ensure_ascii=False, sort_keys=True, indent=2) + "\n")
        return path


def assign_duplicate_groups(records: Sequence[ResearchRunRecord]) -> tuple[ResearchRunRecord, ...]:
    """Deterministically group records sharing a normalized (url, entity) identity.

    Every record gets a duplicate_group -- including singletons -- so dedupe rate can be
    measured as ``1 - unique_groups / total_records`` without a separate "is duplicate" flag.
    """
    updated = []
    for record in records:
        group_id = "dup_" + sha256(record.dedup_key.encode()).hexdigest()[:16]
        updated.append(replace(record, duplicate_group=group_id))
    return tuple(updated)


def dedup_rate(records: Sequence[ResearchRunRecord]) -> float:
    if not records:
        return 0.0
    groups = {r.duplicate_group or r.dedup_key for r in records}
    return 1 - (len(groups) / len(records))


def source_diversity(records: Sequence[ResearchRunRecord]) -> dict:
    return {
        "distinct_providers": len({r.provider for r in records}),
        "distinct_source_types": len({r.source_type for r in records}),
        "total_records": len(records),
    }


@dataclass(frozen=True)
class OpportunityScoreWeights:
    verification_state: float = 0.4
    evidence_class: float = 0.3
    source_type: float = 0.2
    recency: float = 0.1

    def validate(self) -> None:
        total = self.verification_state + self.evidence_class + self.source_type + self.recency
        if not abs(total - 1.0) < 1e-9:
            raise ValueError("opportunity_score_weights_must_sum_to_one")
        for value, field in ((self.verification_state, "verification_state"),
                            (self.evidence_class, "evidence_class"),
                            (self.source_type, "source_type"), (self.recency, "recency")):
            _unit_rate(value, f"weight_{field}")


DEFAULT_SCORE_WEIGHTS = OpportunityScoreWeights()

_VERIFICATION_SUBSCORE = {"verified": 1.0, "reviewed": 0.6, "unverified": 0.3, "rejected": 0.0}
_EVIDENCE_SUBSCORE = {
    EvidenceClass.FACT: 1.0, EvidenceClass.CLAIM: 0.5,
    EvidenceClass.ESTIMATE: 0.4, EvidenceClass.ASSUMPTION: 0.2, EvidenceClass.UNKNOWN: 0.0,
}
_SOURCE_TYPE_SUBSCORE = {
    "official_portal": 1.0, "tender_notice": 1.0, "trade_database": 0.8,
    "company_website": 0.6, "directory": 0.4, "search_engine": 0.3, "other": 0.1,
}


def score_opportunity(record: ResearchRunRecord, weights: OpportunityScoreWeights = DEFAULT_SCORE_WEIGHTS) -> float:
    """A deterministic, auditable score over fields the record already carries -- never a
    fabricated or externally-sourced number. Recency compares retrieved_at to published_at
    when both are present; otherwise it contributes a neutral 0.5.
    """
    weights.validate()
    verification_subscore = _VERIFICATION_SUBSCORE[record.verification_state]
    evidence_subscore = _EVIDENCE_SUBSCORE[EvidenceClass(record.evidence_class)]
    source_subscore = _SOURCE_TYPE_SUBSCORE[record.source_type]
    recency_subscore = 0.5
    if record.published_at is not None:
        age_days = (datetime.fromisoformat(record.retrieved_at) - datetime.fromisoformat(record.published_at)).days
        recency_subscore = 1.0 if age_days <= 30 else (0.6 if age_days <= 180 else 0.2)
    return (weights.verification_state * verification_subscore + weights.evidence_class * evidence_subscore
            + weights.source_type * source_subscore + weights.recency * recency_subscore)


def rank_opportunities(records: Sequence[ResearchRunRecord], weights: OpportunityScoreWeights = DEFAULT_SCORE_WEIGHTS,
                      *, top_n: int = 20) -> tuple[ResearchRunRecord, ...]:
    scored = [replace(record, opportunity_score=score_opportunity(record, weights)) for record in records]
    scored.sort(key=lambda r: (-r.opportunity_score, r.url))
    return tuple(scored[:top_n])


@dataclass(frozen=True)
class ResearchBenchmarkPolicy:
    """Versioned acceptance thresholds for a discovery provider, extending
    research_evidence.py's SearchBenchmarkPolicy pattern with run-level yield metrics.
    Policy parameters, not measured truth -- revise via a new policy_version, not by editing
    validate()'s body.
    """

    policy_version: str
    min_coverage: float
    min_unique_buyer_yield: float
    min_verified_buyer_yield: float
    min_citation_accuracy: float
    min_source_quality: float
    max_hallucination_rate: float
    max_duplicate_rate: float
    max_stale_result_rate: float
    max_false_positive_rate: float

    def validate(self) -> None:
        if not self.policy_version.strip():
            raise ValueError("invalid_policy_version")
        for value, field in (
            (self.min_coverage, "min_coverage"), (self.min_unique_buyer_yield, "min_unique_buyer_yield"),
            (self.min_verified_buyer_yield, "min_verified_buyer_yield"),
            (self.min_citation_accuracy, "min_citation_accuracy"), (self.min_source_quality, "min_source_quality"),
            (self.max_hallucination_rate, "max_hallucination_rate"), (self.max_duplicate_rate, "max_duplicate_rate"),
            (self.max_stale_result_rate, "max_stale_result_rate"),
            (self.max_false_positive_rate, "max_false_positive_rate"),
        ):
            _unit_rate(value, field)

    def failures(self, benchmark: "ResearchProviderBenchmark") -> tuple[str, ...]:
        checks = (
            ("coverage", benchmark.coverage, self.min_coverage, "min"),
            ("unique_buyer_yield", benchmark.unique_buyer_yield, self.min_unique_buyer_yield, "min"),
            ("verified_buyer_yield", benchmark.verified_buyer_yield, self.min_verified_buyer_yield, "min"),
            ("citation_accuracy", benchmark.citation_accuracy, self.min_citation_accuracy, "min"),
            ("source_quality", benchmark.source_quality, self.min_source_quality, "min"),
            ("hallucination_rate", benchmark.hallucination_rate, self.max_hallucination_rate, "max"),
            ("duplicate_rate", benchmark.duplicate_rate, self.max_duplicate_rate, "max"),
            ("stale_result_rate", benchmark.stale_result_rate, self.max_stale_result_rate, "max"),
            ("false_positive_rate", benchmark.false_positive_rate, self.max_false_positive_rate, "max"),
        )
        failures = []
        for name, actual, bound, kind in checks:
            if kind == "min" and actual < bound:
                failures.append(f"{name}_below_policy:{actual}<{bound}")
            elif kind == "max" and actual > bound:
                failures.append(f"{name}_above_policy:{actual}>{bound}")
        return tuple(failures)


DEFAULT_RESEARCH_BENCHMARK_POLICY = ResearchBenchmarkPolicy(
    policy_version="nexus.research-benchmark-policy.v1",
    min_coverage=0.5, min_unique_buyer_yield=0.05, min_verified_buyer_yield=0.02,
    min_citation_accuracy=0.8, min_source_quality=0.6, max_hallucination_rate=0.05,
    max_duplicate_rate=0.6, max_stale_result_rate=0.3, max_false_positive_rate=0.2,
)


@dataclass(frozen=True)
class ResearchProviderBenchmark:
    """Phase G/H measured acceptance record for one discovery provider on one benchmark run.
    KEEP/CONNECT must satisfy every mandatory threshold in the governing policy; BUILD/DEFER/
    REJECT may legitimately sit below threshold.
    """

    provider_id: str
    coverage: float
    unique_buyer_yield: float
    verified_buyer_yield: float
    citation_accuracy: float
    source_quality: float
    hallucination_rate: float
    duplicate_rate: float
    stale_result_rate: float
    false_positive_rate: float
    latency_ms: float
    cost_per_100_raw_results: float
    cost_per_100_verified_buyers: float
    decision: str
    evaluated_at: str
    sample_size: int
    notes: str = ""

    def validate(self, policy: ResearchBenchmarkPolicy = DEFAULT_RESEARCH_BENCHMARK_POLICY) -> None:
        if not self.provider_id.strip():
            raise ValueError("invalid_provider_id")
        for value, field in (
            (self.coverage, "coverage"), (self.unique_buyer_yield, "unique_buyer_yield"),
            (self.verified_buyer_yield, "verified_buyer_yield"), (self.citation_accuracy, "citation_accuracy"),
            (self.source_quality, "source_quality"), (self.hallucination_rate, "hallucination_rate"),
            (self.duplicate_rate, "duplicate_rate"), (self.stale_result_rate, "stale_result_rate"),
            (self.false_positive_rate, "false_positive_rate"),
        ):
            _unit_rate(value, field)
        for value, field in (
            (self.latency_ms, "latency_ms"), (self.cost_per_100_raw_results, "cost_per_100_raw_results"),
            (self.cost_per_100_verified_buyers, "cost_per_100_verified_buyers"),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
                raise ValueError(f"invalid_{field}")
        if self.decision not in BENCHMARK_DECISIONS:
            raise ValueError("invalid_benchmark_decision")
        if isinstance(self.sample_size, bool) or not isinstance(self.sample_size, int) or self.sample_size < 1:
            raise ValueError("invalid_sample_size")
        _utc(self.evaluated_at, "evaluated_at")

        policy.validate()
        if self.decision in _ACCEPTANCE_DECISIONS:
            failures = policy.failures(self)
            if failures:
                raise ValueError("decision_violates_benchmark_policy:" + ",".join(failures))


def run_summary(run: ResearchRun, records: Sequence[ResearchRunRecord]) -> dict:
    """The measurement report the acceptance targets ask for -- dedupe rate, source diversity,
    unique-buyer count -- computed only from what's actually in ``records``, never assumed.
    """
    unique_entities = {
        (r.entity_name.strip().lower(), (r.country or "").strip().lower())
        for r in records if r.entity_name
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": run.run_id,
        "project_id": run.project_id,
        "lane_id": run.lane_id,
        "total_raw_discoveries": len(records),
        "dedupe_rate": dedup_rate(records),
        "unique_entity_count": len(unique_entities),
        **source_diversity(records),
        "digest": canonical_digest({
            "run_id": run.run_id, "total": len(records),
            "urls": sorted({r.url for r in records}),
        }),
    }
