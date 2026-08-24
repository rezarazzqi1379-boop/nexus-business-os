from __future__ import annotations

from .graph import BrainGraph
from .model import AuthorityTier, EpistemicStatus, Node, NodeType


def _node(id: str, type: NodeType, label: str, project_id: str, tier: AuthorityTier, status: EpistemicStatus, source: str | None = None, **attrs) -> Node:
    refs = (source,) if source else ()
    return Node(
        id=id,
        type=type,
        label=label,
        project_id=project_id,
        authority_tier=tier,
        epistemic_status=status,
        source_refs=refs,
        attributes=attrs,
    )


def canonical_portfolio_graph() -> BrainGraph:
    """Small authority-aligned portfolio fixture for acceptance and UI development.

    This fixture is implementation/test data. Canonical project masters remain authority.
    """
    nodes: list[Node] = []

    # Hydrostatic Tester — PRJ-HYD-01
    p = "PRJ-HYD-01"
    src = "PRJ-HYD-01-ENG:v1.1"
    nodes.extend([
        _node("HYD-PROJECT", NodeType.PROJECT, "OCTG Hydrostatic Tester", p, AuthorityTier.A, EpistemicStatus.FACT, src),
        _node("HYD-OD", NodeType.REQUIREMENT, "OD 89-180 mm", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="hydrotester", predicate="buyer_od_mm", value="89-180", governing=True),
        _node("HYD-WT", NodeType.REQUIREMENT, "WT 6-20 mm", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="hydrotester", predicate="buyer_wt_mm", value="6-20", governing=True),
        _node("HYD-LEN", NodeType.REQUIREMENT, "Length 9-12 m", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="hydrotester", predicate="buyer_length_m", value="9-12", governing=True),
        _node("HYD-PMAX", NodeType.REQUIREMENT, "Up to 120 MPa duty-dependent", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="hydrotester", predicate="buyer_max_pressure_mpa", value=120, governing=True),
        _node("HYD-HOLD", NodeType.REQUIREMENT, "Hold 5-10 s", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="hydrotester", predicate="buyer_hold_time_s", value="5-10", governing=True),
        _node("HYD-TPH", NodeType.REQUIREMENT, "60 pipes/hour buyer basis", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="hydrotester", predicate="buyer_throughput_pipes_per_hour", value=60, governing=True),
        _node("HYD-UNK-MATRIX", NodeType.REQUIREMENT, "Signed critical duty matrix", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
        _node("HYD-UNK-FAT", NodeType.REQUIREMENT, "Final FAT/TPI/ITP and pass-fail basis", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
    ])

    # KCl / White MOP — PRJ-KCL-01
    p = "PRJ-KCL-01"
    src = "PRJ-KCL-01-ACC:v1.0"
    nodes.extend([
        _node("KCL-PROJECT", NodeType.PROJECT, "KCl / White MOP for SOP Feed", p, AuthorityTier.A, EpistemicStatus.FACT, src),
        _node("KCL-MOIST", NodeType.REQUIREMENT, "Moisture max 0.5%", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="moisture_max_percent", value=0.5, governing=True),
        _node("KCL-K2O", NodeType.REQUIREMENT, "K2O min 61%", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="k2o_min_percent", value=61, governing=True),
        _node("KCL-NACL", NodeType.REQUIREMENT, "NaCl max 2%", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="nacl_max_percent", value=2, governing=True),
        _node("KCL-MGCL2", NodeType.REQUIREMENT, "MgCl2 max 1%", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="mgcl2_max_percent", value=1, governing=True),
        _node("KCL-SOL", NodeType.REQUIREMENT, "Solubility min 99.5%", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="solubility_min_percent", value=99.5, governing=True),
        _node("KCL-PSD", NodeType.REQUIREMENT, "Granulometry acceptance window", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="granulometry", value="75% at 0.1-0.4 mm; 1 mm max 0.5%; below 0.1 mm max 23.5%", governing=True),
        _node("KCL-REF-62", NodeType.CLAIM, "62% White Fine Grade A is preference/reference, not minimum", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="kcl", predicate="preferred_reference_grade", value="62% K2O White Fine Grade A"),
        _node("KCL-UNK-DEMAND", NodeType.REQUIREMENT, "Current purchase quantity / forecast", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
        _node("KCL-UNK-PERMIT", NodeType.RISK, "Current permit/legal applicability", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
        _node("KCL-UNK-COMM", NodeType.REQUIREMENT, "Current destination/Incoterm/payment/logistics", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
    ])

    # Heat Treatment — PRJ-HTL-01
    p = "PRJ-HTL-01"
    src = "PRJ-HTL-01-ENG:v1.1"
    nodes.extend([
        _node("HTL-PROJECT", NodeType.PROJECT, "OCTG Heat Treatment Line", p, AuthorityTier.A, EpistemicStatus.FACT, src),
        _node("HTL-OD", NodeType.REQUIREMENT, "OD 63.5-177.8 mm", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="heat-treatment", predicate="od_mm", value="63.5-177.8", governing=True),
        _node("HTL-WT", NodeType.REQUIREMENT, "WT 2-20 mm", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="heat-treatment", predicate="wall_thickness_mm", value="2-20", governing=True),
        _node("HTL-LEN", NodeType.REQUIREMENT, "Length 6-12 m", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="heat-treatment", predicate="length_m", value="6-12", governing=True),
        _node("HTL-PROC", NodeType.REQUIREMENT, "Quench + Normalize + Temper", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="heat-treatment", predicate="process", value="quench+normalize+temper", governing=True),
        _node("HTL-TPH-WORK", NodeType.CLAIM, "Current working throughput ~40 pipes/hour", p, AuthorityTier.C, EpistemicStatus.INFERENCE, "cross-chat-reconciliation:stage5", subject="heat-treatment", predicate="throughput_assertion", value="~40 pipes/hour"),
        _node("HTL-TPM-HIST", NodeType.CLAIM, "Historical engineer message 40-60 pipes/minute", p, AuthorityTier.B, EpistemicStatus.CLAIM, "engineer-message:historical", subject="heat-treatment", predicate="throughput_assertion", value="40-60 pipes/minute"),
        _node("HTL-UNK-REVALIDATE", NodeType.REQUIREMENT, "Buyer engineering throughput revalidation", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
    ])

    # Can / Tube End Forming — PRJ-CAN-01
    p = "PRJ-CAN-01"
    src = "PRJ-CAN-01-ENG:v1.0"
    nodes.extend([
        _node("CAN-PROJECT", NodeType.PROJECT, "Can / Tube End Forming", p, AuthorityTier.A, EpistemicStatus.FACT, src),
        _node("CAN-RANGE", NodeType.REQUIREMENT, "Approx. diameter 52-99 mm", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="can-forming", predicate="diameter_mm", value="52-99", governing=True),
        _node("CAN-SCOPE-A", NodeType.REQUIREMENT, "Scope A: necking-only", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="can-forming", predicate="scope_a", value="necking-only", governing=True),
        _node("CAN-SCOPE-B", NodeType.REQUIREMENT, "Scope B: full forming", p, AuthorityTier.A, EpistemicStatus.FACT, src, subject="can-forming", predicate="scope_b", value="necking+flanging+beading", governing=True),
        _node("CAN-GE-MAX", NodeType.CLAIM, "Golden Eagle 500 CPM MAX", p, AuthorityTier.B, EpistemicStatus.CLAIM, "Golden-Eagle:D73-D99-proposal-evidence", subject="golden-eagle", predicate="max_cpm_claim", value=500),
        _node("CAN-GE-STABLE", NodeType.CLAIM, "Golden Eagle 400 CPM stable statement", p, AuthorityTier.B, EpistemicStatus.CLAIM, "supplier-email:golden-eagle", subject="golden-eagle", predicate="stable_cpm_claim", value=400),
        _node("CAN-UNK-SCOPEA", NodeType.REQUIREMENT, "Separate necking-only technical/commercial offer", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
        _node("CAN-UNK-LINEBAL", NodeType.REQUIREMENT, "Compatibility / line-balancing with existing line", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
        _node("CAN-UNK-FAT", NodeType.REQUIREMENT, "Stable-speed FAT method and acceptance", p, AuthorityTier.C, EpistemicStatus.UNKNOWN, None, blocking=True),
    ])

    return BrainGraph(nodes=nodes)
