from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AuthorityTier(str, Enum):
    A = "canonical_authority"
    B = "live_evidence"
    C = "operational_state"
    D = "research_claim"


class EpistemicStatus(str, Enum):
    FACT = "fact"
    CLAIM = "claim"
    ESTIMATE = "estimate"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    ASSUMPTION = "assumption"
    UNKNOWN = "unknown"
    CONTRADICTED = "contradicted"
    STALE = "stale"
    SUPERSEDED = "superseded"


class NodeType(str, Enum):
    PROJECT = "project"
    COMPANY = "company"
    PERSON = "person"
    PRODUCT = "product"
    REQUIREMENT = "requirement"
    CLAIM = "claim"
    EVIDENCE = "evidence"
    DECISION = "decision"
    ACTION = "action"
    OUTCOME = "outcome"
    OPPORTUNITY = "opportunity"
    COMMUNICATION = "communication"
    CONNECTOR = "connector"
    ARTIFACT = "artifact"
    RISK = "risk"


@dataclass(frozen=True)
class Node:
    id: str
    type: NodeType
    label: str
    project_id: str | None = None
    authority_tier: AuthorityTier = AuthorityTier.D
    epistemic_status: EpistemicStatus = EpistemicStatus.UNKNOWN
    source_refs: tuple[str, ...] = ()
    observed_at: str | None = None
    verified_at: str | None = None
    review_at: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    superseded_by: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Edge:
    id: str
    from_id: str
    relation: str
    to_id: str
    source_refs: tuple[str, ...] = ()
    observed_at: str | None = None
    valid_from: str | None = None
    valid_to: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
