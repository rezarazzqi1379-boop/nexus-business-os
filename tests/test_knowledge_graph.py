from nexus_core.knowledge_graph import (
    EpistemicState,
    GraphEdge,
    GraphNode,
    NodeKind,
    PromotionTarget,
    decide_promotion,
    validate_edge,
    validate_node,
)


def test_hypothesis_is_kept_in_exploration_but_not_decision_support():
    node = GraphNode(
        node_id="sig-1",
        kind=NodeKind.SIGNAL,
        label="possible plant upgrade",
        epistemic_state=EpistemicState.HYPOTHESIS,
        source_refs=("exa:result-1",),
        project_refs=("hydrotester",),
        confidence=0.6,
    )
    assert decide_promotion(node, target=PromotionTarget.EXPLORATION).allowed
    decision = decide_promotion(node, target=PromotionTarget.DECISION_SUPPORT)
    assert not decision.allowed
    assert "decision_support_requires_fact" in decision.reasons


def test_hypothesis_with_project_linkage_can_enter_experiment():
    node = GraphNode(
        node_id="hyp-1",
        kind=NodeKind.IDEA,
        label="Turkey pipe expansion predicts hydrotest demand",
        epistemic_state=EpistemicState.HYPOTHESIS,
        source_refs=("source:a",),
        project_refs=("hydrotester",),
        confidence=0.4,
    )
    assert decide_promotion(node, target=PromotionTarget.EXPERIMENT).allowed


def test_invalid_or_duplicate_provenance_fails_closed():
    node = GraphNode(
        node_id="x",
        kind=NodeKind.PAPER,
        label="paper",
        epistemic_state=EpistemicState.CLAIM,
        source_refs=("doi:1", "doi:1"),
    )
    assert "invalid_source_refs" in validate_node(node)


def test_unknown_edge_endpoints_are_rejected():
    edge = GraphEdge(
        edge_id="e1",
        source_node_id="a",
        target_node_id="missing",
        relation="supports",
        source_refs=("source:1",),
        epistemic_state=EpistemicState.CLAIM,
    )
    assert "unknown_edge_endpoint" in validate_edge(edge, known_node_ids={"a"})


def test_fact_requires_high_confidence_for_decision_support():
    node = GraphNode(
        node_id="fact-1",
        kind=NodeKind.COMPANY,
        label="verified manufacturer",
        epistemic_state=EpistemicState.FACT,
        source_refs=("official:company",),
        project_refs=("octg",),
        confidence=0.79,
    )
    decision = decide_promotion(node, target=PromotionTarget.DECISION_SUPPORT)
    assert not decision.allowed
    assert "insufficient_confidence" in decision.reasons
