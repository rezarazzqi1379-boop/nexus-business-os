from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class SourceHealth:
    source_id: str
    available: bool
    read_only: bool
    auth_error: bool
    cost_per_query: float
    evidence_ref: str


@dataclass(frozen=True)
class SourceRoute:
    selected: tuple[str, ...]
    skipped: tuple[tuple[str, str], ...]


def _validate(source: SourceHealth) -> None:
    if not source.source_id.strip() or not source.evidence_ref.strip():
        raise ValueError("invalid_source_health")
    if not isinstance(source.available, bool) or not isinstance(source.read_only, bool) or not isinstance(source.auth_error, bool):
        raise ValueError("invalid_source_boolean")
    if isinstance(source.cost_per_query, bool) or not isinstance(source.cost_per_query, (int, float)) or source.cost_per_query < 0:
        raise ValueError("invalid_source_cost")


def route_read_sources(
    sources: Iterable[SourceHealth], *, max_sources: int = 3, max_cost: float = 0.0
) -> SourceRoute:
    """Select healthy read-only sources; unavailable/auth-broken providers never block the lane."""
    if not 1 <= max_sources <= 10 or max_cost < 0:
        raise ValueError("invalid_route_budget")
    items = tuple(sources)
    seen: set[str] = set()
    selected: list[str] = []
    skipped: list[tuple[str, str]] = []
    spent = 0.0
    for source in sorted(items, key=lambda item: (item.cost_per_query, item.source_id)):
        _validate(source)
        if source.source_id in seen:
            raise ValueError("duplicate_source_health")
        seen.add(source.source_id)
        if source.auth_error:
            skipped.append((source.source_id, "authentication_failed"))
        elif not source.available:
            skipped.append((source.source_id, "unavailable"))
        elif not source.read_only:
            skipped.append((source.source_id, "write_scope_not_allowed"))
        elif spent + source.cost_per_query > max_cost:
            skipped.append((source.source_id, "cost_budget_exceeded"))
        elif len(selected) >= max_sources:
            skipped.append((source.source_id, "source_limit"))
        else:
            selected.append(source.source_id)
            spent += source.cost_per_query
    if not selected:
        skipped.append(("route", "no_safe_source"))
    return SourceRoute(tuple(selected), tuple(skipped))


@dataclass(frozen=True)
class ReachPreflight:
    """Routing advice only; never installs software or performs network calls."""
    route: str
    reason: str
    project_id: str
    lane_id: str
    max_queries: int = 2
    max_results: int = 5
    excerpt_chars: int = 1200


def agent_reach_preflight(*, project_id: str, lane_id: str,
                          needs_external_evidence: bool, sensitivity: str,
                          native_available: bool, cache_fresh: bool,
                          reach_healthy: bool, health_age_seconds: float,
                          remaining_queries: int) -> ReachPreflight:
    """Cheap mandatory decision; execution is optional and separately governed.

    Call from the existing research/connector entry point. A health observation
    is caller-supplied evidence, not a claim that this helper ran doctor.
    """
    import math
    if not project_id.strip() or not lane_id.strip():
        raise ValueError("project_and_lane_required")
    flags = (needs_external_evidence, native_available, cache_fresh, reach_healthy)
    if any(type(flag) is not bool for flag in flags):
        raise ValueError("invalid_boolean")
    if sensitivity not in {"public", "internal", "confidential", "restricted"}:
        raise ValueError("invalid_sensitivity")
    if type(remaining_queries) is not int or remaining_queries < 0:
        raise ValueError("invalid_query_budget")
    if (isinstance(health_age_seconds, bool) or
        not isinstance(health_age_seconds, (int, float)) or
        not math.isfinite(health_age_seconds) or health_age_seconds < 0):
        raise ValueError("invalid_health_age")
    route, reason = "skip", "local_work"
    if needs_external_evidence:
        if sensitivity != "public":
            route, reason = "native_only", "private_data_not_for_reach"
        elif cache_fresh:
            route, reason = "cache", "fresh_project_scoped_evidence"
        elif native_available:
            route, reason = "native", "existing_connector_first"
        elif remaining_queries == 0:
            route, reason = "blocked", "query_budget_exhausted"
        elif reach_healthy and health_age_seconds <= 3600:
            route, reason = "agent_reach", "healthy_public_fallback"
        else:
            route, reason = "blocked", "reach_health_missing_or_stale"
    return ReachPreflight(route, reason, project_id, lane_id,
                          max_queries=min(2, remaining_queries))


class ReachReadSession:
    """Bounded acquisition through an explicitly supplied, approved read adapter.

    No network backend is inferred or installed. Reader must enforce public URL,
    redirect, response byte and timeout policies. Only capped excerpts leave
    this session; store full material in the existing evidence store if needed.
    """
    def __init__(self, decision: ReachPreflight, reader):
        if decision.route != "agent_reach" or not callable(reader):
            raise ValueError("approved_reach_route_and_reader_required")
        if not 0 <= decision.max_queries <= 2 or not 1 <= decision.excerpt_chars <= 1200:
            raise ValueError("invalid_read_budget")
        self.decision = decision
        self.reader = reader
        self.remaining = decision.max_queries
        self.seen = set()

    def read(self, url: str) -> dict:
        from urllib.parse import urlsplit
        import hashlib
        from datetime import datetime, timezone
        parsed = urlsplit(url)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
            parsed.password or parsed.query or parsed.fragment):
            raise ValueError("public_https_url_without_credentials_or_query_required")
        if url in self.seen:
            return {"status": "duplicate", "project_id": self.decision.project_id,
                    "lane_id": self.decision.lane_id}
        if self.remaining <= 0:
            raise ValueError("read_budget_exhausted")
        self.remaining -= 1  # failed attempts consume budget too
        self.seen.add(url)
        body = self.reader(url)
        if not isinstance(body, str):
            raise ValueError("reader_text_required")
        return {"status": "retrieved", "classification": "CLAIM",
                "project_id": self.decision.project_id, "lane_id": self.decision.lane_id,
                "source_url": url, "provider": "agent_reach",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "content_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "excerpt": body[:self.decision.excerpt_chars],
                "truncated": len(body) > self.decision.excerpt_chars}
