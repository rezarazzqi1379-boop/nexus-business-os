"""Sandbox adapter: changed evidence -> existing graph, never commercial authority.

The caller owns acquisition, persistence and model execution. This module has no
network or external writes. A cache hit avoids extraction, not freshness checks.
"""
from dataclasses import dataclass
from hashlib import sha256
from intelligence_graph import Node, link

VERSION = "nexus.incremental-intelligence.v1"


@dataclass(frozen=True)
class Observation:
    project_id: str
    lane: str
    source_ref: str
    origin_id: str
    observed_at: str
    payload: bytes
    extractor_version: str

    def validate(self):
        if not all(isinstance(x, str) and x.strip() for x in (
            self.project_id, self.lane, self.source_ref, self.origin_id,
            self.observed_at, self.extractor_version)) or not isinstance(self.payload, bytes):
            raise ValueError("invalid_observation")

    @property
    def key(self):
        self.validate()
        return (self.project_id, self.lane, self.source_ref, self.extractor_version)

    @property
    def digest(self):
        return sha256(self.payload).hexdigest()


@dataclass(frozen=True)
class Revision:
    observation: Observation
    digest: str
    previous_digest: str | None


def ingest(history: tuple[Revision, ...], observation: Observation):
    """Append changed content; retain lineage; return extraction decision."""
    key = observation.key
    prior = next((r for r in reversed(history) if r.observation.key == key), None)
    if prior and prior.digest == observation.digest and prior.observation.origin_id == observation.origin_id:
        return history, "CACHE_HIT_REVALIDATE_FRESHNESS"
    revision = Revision(observation, observation.digest, prior.digest if prior else None)
    return history + (revision,), "EXTRACT_CHANGED"


def candidate_edge(revision: Revision, buyer: str, item: str, *, project_id: str, lane: str):
    o = revision.observation
    if (o.project_id, o.lane) != (project_id, lane):
        raise ValueError("cross_scope_blocked")
    if revision.digest != o.digest:
        raise ValueError("digest_mismatch")
    ref = f"{o.source_ref}#sha256={revision.digest};origin={o.origin_id};extractor={o.extractor_version}"
    a = Node(buyer, "BUYER", project_id, o.observed_at, ref, "CLAIM")
    b = Node(item, "ITEM", project_id, o.observed_at, ref, "CLAIM")
    return link(a, b, "POSSIBLE_DEMAND", ref)


@dataclass
class RetrievalBudget:
    max_queries: int
    max_estimated_tokens: int
    low_yield_limit: int = 2
    queries: int = 0
    estimated_tokens: int = 0
    low_yield_streak: int = 0

    def __post_init__(self):
        if any(type(x) is not int or x < 1 for x in (
            self.max_queries, self.max_estimated_tokens, self.low_yield_limit)):
            raise ValueError("invalid_budget")

    def reserve(self, estimated_tokens: int):
        if type(estimated_tokens) is not int or estimated_tokens < 1:
            raise ValueError("invalid_token_estimate")
        if self.low_yield_streak >= self.low_yield_limit:
            return "STOP_LOW_YIELD"
        if self.queries >= self.max_queries or self.estimated_tokens + estimated_tokens > self.max_estimated_tokens:
            return "STOP_BUDGET"
        self.queries += 1
        self.estimated_tokens += estimated_tokens
        return "RESERVED"

    def observe_yield(self, unique_qualified_hits: int):
        if type(unique_qualified_hits) is not int or unique_qualified_hits < 0:
            raise ValueError("invalid_yield")
        self.low_yield_streak = 0 if unique_qualified_hits else self.low_yield_streak + 1


def model_route(*, changed: bool, ambiguous: bool):
    """Routing policy only; no claim that either model was invoked."""
    return "STRONG_REVIEW" if changed and ambiguous else "CHEAP_TRIAGE" if changed else "SKIP"
