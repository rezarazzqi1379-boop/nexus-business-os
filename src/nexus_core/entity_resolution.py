from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

from .knowledge_graph import GraphNode, NodeKind


_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def normalize_identity(value: str) -> str:
    """Return a conservative comparable identity token.

    Resolution intentionally avoids fuzzy/ML merging at this layer. False merges
    are more damaging than unresolved duplicates because they contaminate evidence
    lineage across projects. More aggressive matching can be an experiment later.
    """
    text = unicodedata.normalize("NFKC", value).casefold().strip()
    text = text.replace("&", " and ")
    text = _NON_ALNUM.sub(" ", text)
    return " ".join(text.split())


@dataclass(frozen=True)
class ResolutionCandidate:
    canonical_node_id: str
    duplicate_node_id: str
    reason: str


def find_exact_identity_duplicates(nodes: tuple[GraphNode, ...]) -> tuple[ResolutionCandidate, ...]:
    """Find deterministic duplicate candidates without mutating the graph."""
    seen: dict[tuple[NodeKind, str], str] = {}
    duplicates: list[ResolutionCandidate] = []
    for node in sorted(nodes, key=lambda item: item.node_id):
        identity = normalize_identity(node.label)
        if not identity:
            continue
        key = (node.kind, identity)
        canonical = seen.get(key)
        if canonical is None:
            seen[key] = node.node_id
            continue
        duplicates.append(
            ResolutionCandidate(
                canonical_node_id=canonical,
                duplicate_node_id=node.node_id,
                reason="exact_normalized_kind_and_label",
            )
        )
    return tuple(duplicates)
