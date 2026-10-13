"""Offline vertical adapter: scoped observations -> reviewed commercial graph.

Structured source claims are untrusted. Reviews and legal identities must come
from the caller's trusted review store, never from the source payload. This
adapter neither acquires sources nor approves/executes commercial actions.
Live connector callers still require nexus_chat_bootstrap before invoking it.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Mapping

from incremental_intelligence import Observation, Revision, candidate_edge, ingest
from intelligence_graph import Edge, Node, link
from policy import decide_action
from steel_commercial_intelligence import EvidenceKind, IntelEdge, current_demand_ready

TRIGGERS = frozenset({"CURRENT_RFQ", "CURRENT_TENDER", "CURRENT_PROCUREMENT_NEED", "CURRENT_STOCK_NEED"})


def utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timezone_required")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class RelationshipReview:
    project_id: str
    lane: str
    source_ref: str
    digest: str
    origin_id: str  # canonical publisher family, including mirrors
    buyer_id: str
    legal_id: str
    product_id: str
    relation: str
    reviewed_at: str
    valid_until: str
    reviewer_ref: str


@dataclass(frozen=True)
class ProofResult:
    history: tuple[Revision, ...]
    graph: tuple[Edge, ...]
    commercial_edges: tuple[IntelEdge, ...]
    ready_for_research: bool
    extraction_count: int
    extraction_bytes: int
    rejection_reasons: tuple[str, ...]
    model_tokens: int = 0  # deterministic JSON extraction; no model invocation


def prove_relationship(observations: tuple[Observation, ...], *,
                       project_id: str, lane: str, buyer_id: str, product_id: str,
                       legal_identities: Mapping[str, str],
                       reviews: tuple[RelationshipReview, ...], as_of: str,
                       history: tuple[Revision, ...] = (), action: str = "research",
                       max_age_days: int = 30, max_bytes: int = 65536) -> ProofResult:
    """Return a research-qualified relationship; never transaction authority.

    Scope/action/input-budget errors reject the entire batch before ingestion.
    Missing, expired or mismatched reviews leave source edges as HYPOTHESIS.
    Cache hits are revalidated against current time and review state on every run.
    """
    if action != "research" or decide_action(action).disposition != "allow":
        raise ValueError("proof_is_research_only")
    if not all(x.strip() for x in (project_id, lane, buyer_id, product_id)):
        raise ValueError("scope_and_relationship_required")
    if type(max_age_days) is not int or max_age_days < 1 or type(max_bytes) is not int or max_bytes < 1:
        raise ValueError("invalid_budget")
    now = utc(as_of)
    revisions_by_key = {}
    for observation in observations:
        observation.validate()
        if (observation.project_id, observation.lane) != (project_id, lane):
            raise ValueError("cross_scope_blocked")
        signature = (observation.digest, observation.origin_id)
        if observation.key in revisions_by_key and revisions_by_key[observation.key] != signature:
            raise ValueError("conflicting_batch_revision")
        revisions_by_key[observation.key] = signature
    if sum(len(o.payload) for o in observations) > max_bytes:
        raise ValueError("input_budget_exceeded")
    graph, commercial, rejected = [], [], []
    seen = set()
    count = byte_count = 0
    for observation in observations:
        key = (observation.key, observation.digest, observation.origin_id)
        if key in seen:
            continue
        seen.add(key)
        history, _ = ingest(history, observation)
        # Count actual parsing work, including cache-hit review revalidation.
        count += 1
        byte_count += len(observation.payload)
        revision = next(r for r in reversed(history) if r.observation.key == observation.key)
        edge = candidate_edge(revision, buyer_id, product_id, project_id=project_id, lane=lane)
        graph.append(edge)
        try:
            body = json.loads(observation.payload)
            observed = utc(observation.observed_at)
            if not isinstance(body, dict):
                raise ValueError("structured_claim_required")
            relation = body.get("relation")
            legal_id = legal_identities.get(buyer_id)
            if not legal_id or (body.get("buyer_id"), body.get("legal_id"), body.get("product_id")) != (buyer_id, legal_id, product_id):
                raise ValueError("entity_or_product_mismatch")
            if relation not in TRIGGERS:
                raise ValueError("current_need_relation_required")
            if not now - timedelta(days=max_age_days) <= observed <= now:
                raise ValueError("stale_or_future_source")
            matching = [r for r in reviews if
                        (r.project_id, r.lane, r.source_ref, r.digest, r.origin_id,
                         r.buyer_id, r.legal_id, r.product_id, r.relation) ==
                        (project_id, lane, observation.source_ref, observation.digest,
                         observation.origin_id, buyer_id, legal_id, product_id, relation)
                        and r.reviewer_ref.strip() and observed <= utc(r.reviewed_at) <= now <= utc(r.valid_until)]
            if not matching:
                raise ValueError("current_bound_review_required")
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            rejected.append(str(exc))
            continue
        a = Node(buyer_id, "BUYER", project_id, observation.observed_at, edge.source_id, "CLAIM")
        b = Node(product_id, "ITEM", project_id, observation.observed_at, edge.source_id, "CLAIM")
        graph[-1] = link(a, b, relation, edge.source_id, verified=True)
        # The trusted canonical origin is used for independence, not URL count.
        commercial.append(IntelEdge(project_id, buyer_id, relation, product_id,
                                    observation.origin_id.strip().lower(), observation.observed_at,
                                    EvidenceKind.OBSERVED, True))
    return ProofResult(history, tuple(graph), tuple(commercial),
                       current_demand_ready(tuple(commercial), project_id, buyer_id, product_id),
                       count, byte_count, tuple(rejected))
