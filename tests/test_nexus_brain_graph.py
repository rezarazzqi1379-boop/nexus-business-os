from nexus_brain import AuthorityTier, BrainGraph, Edge, EpistemicStatus, Node, NodeType


def node(
    id,
    *,
    type=NodeType.CLAIM,
    tier=AuthorityTier.D,
    status=EpistemicStatus.CLAIM,
    refs=(),
    project="PRJ-HYD-01",
    **attributes,
):
    return Node(
        id=id,
        type=type,
        label=id,
        project_id=project,
        authority_tier=tier,
        epistemic_status=status,
        source_refs=tuple(refs),
        attributes=attributes,
    )


def test_fact_without_provenance_is_rejected():
    graph = BrainGraph()
    candidate = node(
        "REQ-1",
        type=NodeType.REQUIREMENT,
        tier=AuthorityTier.A,
        status=EpistemicStatus.FACT,
    )
    try:
        graph.add_node(candidate)
    except ValueError as exc:
        assert "source_refs" in str(exc) or "provenance" in str(exc)
    else:
        raise AssertionError("Tier A fact without provenance must fail closed")


def test_cross_project_values_are_isolated():
    graph = BrainGraph(
        nodes=[
            node("HYD", type=NodeType.PROJECT, tier=AuthorityTier.A, status=EpistemicStatus.FACT, refs=("master:hyd",)),
            node(
                "HTL-TPH",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.A,
                status=EpistemicStatus.FACT,
                refs=("master:htl",),
                project="PRJ-HTL-01",
                subject="heat-treatment",
                predicate="throughput_pipes_per_hour",
                value=40,
            ),
        ]
    )
    assert graph.project_nodes("PRJ-HYD-01") == (graph.nodes["HYD"],)
    assert graph.project_nodes("PRJ-HTL-01") == (graph.nodes["HTL-TPH"],)


def test_lower_authority_claim_about_same_assertion_conflicts_with_governing_fact():
    graph = BrainGraph(
        nodes=[
            node(
                "REQ-HYD-PMAX",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.A,
                status=EpistemicStatus.FACT,
                refs=("PRJ-HYD-01-ENG:v1.1",),
                subject="hydrotester-buyer-basis",
                predicate="required_upper_capability_mpa",
                value=120,
                governing=True,
            ),
            node(
                "CLM-BUYER-NEEDS-150",
                tier=AuthorityTier.D,
                status=EpistemicStatus.CLAIM,
                refs=("research:synthetic-conflict-fixture",),
                subject="hydrotester-buyer-basis",
                predicate="required_upper_capability_mpa",
                value=150,
            ),
        ]
    )
    contradictions = graph.detect_value_contradictions("PRJ-HYD-01")
    assert len(contradictions) == 1
    assert contradictions[0].reason == "lower-authority evidence conflicts with governing value"
    assert graph.decision_context("PRJ-HYD-01").consequential_use_allowed is False


def test_supplier_capability_above_requirement_is_not_misclassified_as_same_assertion_conflict():
    graph = BrainGraph(
        nodes=[
            node(
                "REQ-HYD-PMAX",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.A,
                status=EpistemicStatus.FACT,
                refs=("PRJ-HYD-01-ENG:v1.1",),
                subject="hydrotester-buyer-basis",
                predicate="required_upper_capability_mpa",
                value=120,
                governing=True,
            ),
            node(
                "CLM-YAX-PMAX",
                tier=AuthorityTier.D,
                status=EpistemicStatus.CLAIM,
                refs=("brochure:yaxing",),
                subject="yaxing-machine-capability",
                predicate="advertised_max_capability_mpa",
                value=150,
            ),
        ]
    )
    assert graph.detect_value_contradictions("PRJ-HYD-01") == ()


def test_same_authority_conflict_fails_closed():
    graph = BrainGraph(
        nodes=[
            node(
                "REQ-A",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.A,
                status=EpistemicStatus.FACT,
                refs=("master:a",),
                subject="hydrotester-buyer-basis",
                predicate="throughput_pipes_per_hour",
                value=60,
            ),
            node(
                "REQ-B",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.A,
                status=EpistemicStatus.FACT,
                refs=("master:b",),
                subject="hydrotester-buyer-basis",
                predicate="throughput_pipes_per_hour",
                value=50,
            ),
        ]
    )
    context = graph.decision_context("PRJ-HYD-01")
    assert context.consequential_use_allowed is False
    assert "unresolved_contradiction" in context.blockers
    assert context.contradictions[0].reason == "same-authority conflict requires explicit resolution"


def test_blocking_unknown_prevents_consequential_use():
    graph = BrainGraph(
        nodes=[
            node(
                "REQ-PMAX",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.A,
                status=EpistemicStatus.FACT,
                refs=("master:hyd",),
                governing=True,
                subject="hydrotester-buyer-basis",
                predicate="required_upper_capability_mpa",
                value=120,
            ),
            node(
                "UNK-FAT",
                type=NodeType.REQUIREMENT,
                tier=AuthorityTier.C,
                status=EpistemicStatus.UNKNOWN,
                refs=(),
                blocking=True,
            ),
        ]
    )
    context = graph.decision_context("PRJ-HYD-01")
    assert context.consequential_use_allowed is False
    assert "blocking_unknown" in context.blockers


def test_provenance_traces_linked_evidence():
    graph = BrainGraph(
        nodes=[
            node("CLM", refs=("email:123",)),
            node(
                "EV-1",
                type=NodeType.EVIDENCE,
                tier=AuthorityTier.B,
                status=EpistemicStatus.FACT,
                refs=("attachment:proposal",),
            ),
        ],
        edges=[
            Edge(
                id="E-1",
                from_id="CLM",
                relation="supported_by",
                to_id="EV-1",
                source_refs=("email:123",),
            )
        ],
    )
    assert graph.trace_provenance("CLM") == ("attachment:proposal", "email:123")


def test_consequential_edge_requires_provenance():
    graph = BrainGraph(
        nodes=[
            node("SUP", type=NodeType.COMPANY),
            node("DEC", type=NodeType.DECISION),
        ]
    )
    try:
        graph.add_edge(Edge(id="E", from_id="SUP", relation="selects", to_id="DEC"))
    except ValueError as exc:
        assert "provenance" in str(exc)
    else:
        raise AssertionError("consequential edge without provenance must fail closed")
