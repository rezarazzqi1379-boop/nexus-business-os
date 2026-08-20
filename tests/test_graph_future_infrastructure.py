import pytest

from nexus_core.contradictions import AtomicClaim, detect_atomic_contradictions
from nexus_core.entity_resolution import find_exact_identity_duplicates, normalize_identity
from nexus_core.graph_store import InMemoryGraphRepository
from nexus_core.idea_generator import generate_gap_ideas
from nexus_core.knowledge_graph import EpistemicState, GraphEdge, GraphNode, NodeKind


def node(node_id: str, label: str, *, kind=NodeKind.COMPANY, state=EpistemicState.FACT, confidence=0.9):
    return GraphNode(
        node_id=node_id,
        kind=kind,
        label=label,
        epistemic_state=state,
        source_refs=(f"src:{node_id}",),
        project_refs=("project:kcl",),
        confidence=confidence,
    )


def test_repository_rejects_identity_collision_and_unknown_edge():
    repo = InMemoryGraphRepository()
    repo.put_node(node("company:1", "Alpha Pipe"))
    repo.put_node(node("company:1", "Alpha Pipe"))
    with pytest.raises(ValueError, match="node_identity_collision"):
        repo.put_node(node("company:1", "Different Company"))

    with pytest.raises(ValueError, match="unknown_edge_endpoint"):
        repo.put_edge(
            GraphEdge(
                edge_id="edge:1",
                source_node_id="company:1",
                target_node_id="missing",
                relation="supplies",
                source_refs=("src:e1",),
                epistemic_state=EpistemicState.CLAIM,
            )
        )


def test_exact_resolution_is_kind_scoped_and_conservative():
    nodes = (
        node("company:a", "K + S"),
        node("company:b", "K + S"),
        GraphNode(
            node_id="person:c",
            kind=NodeKind.PERSON,
            label="K + S",
            epistemic_state=EpistemicState.UNKNOWN,
            source_refs=("src:c",),
        ),
    )
    assert normalize_identity("  ACME & Co. ") == "acme and co"
    duplicates = find_exact_identity_duplicates(nodes)
    assert len(duplicates) == 1
    assert duplicates[0].canonical_node_id == "company:a"
    assert duplicates[0].duplicate_node_id == "company:b"


def test_direct_contradictions_preserve_both_claims():
    claims = (
        AtomicClaim("claim:1", "company:a", "max_pressure_mpa", "70", ("src:official",)),
        AtomicClaim("claim:2", "company:a", "max_pressure_mpa", "120", ("src:photo",)),
        AtomicClaim("claim:3", "company:a", "country", "China", ("src:official",)),
        AtomicClaim("claim:4", "company:a", "country", "china", ("src:other",)),
    )
    contradictions = detect_atomic_contradictions(claims)
    assert len(contradictions) == 1
    assert contradictions[0].claim_ids == ("claim:1", "claim:2")
    assert contradictions[0].values == ("70", "120")


def test_idea_generation_uses_graph_gaps_not_unlinked_noise():
    subject = node("company:a", "Boyu", confidence=0.95)
    signal = GraphNode(
        node_id="signal:120mpa",
        kind=NodeKind.SIGNAL,
        label="Possible 120 MPa variant",
        epistemic_state=EpistemicState.HYPOTHESIS,
        source_refs=("src:photo",),
        project_refs=("project:hydrotester",),
        confidence=0.4,
    )
    unlinked = GraphNode(
        node_id="signal:noise",
        kind=NodeKind.SIGNAL,
        label="Interesting but unlinked",
        epistemic_state=EpistemicState.UNKNOWN,
        source_refs=("src:noise",),
        project_refs=(),
        confidence=0.1,
    )
    contradictions = detect_atomic_contradictions(
        (
            AtomicClaim("claim:1", "company:a", "max_pressure_mpa", "70", ("src:official",)),
            AtomicClaim("claim:2", "company:a", "max_pressure_mpa", "120", ("src:photo",)),
        )
    )
    ideas = generate_gap_ideas(nodes=(subject, signal, unlinked), contradictions=contradictions)
    ids = {idea.idea_id for idea in ideas}
    assert "idea:resolve:company:a:max_pressure_mpa" in ids
    assert "idea:verify:signal:120mpa" in ids
    assert "idea:verify:signal:noise" not in ids
