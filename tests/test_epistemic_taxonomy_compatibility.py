from typing import get_args

from nexus_core.decision_learning import EpistemicClass
from nexus_verticals.procurement import EvidenceKind


def test_procurement_and_decision_learning_epistemic_taxonomies_match():
    """Temporary integration guard until taxonomy ownership is formally decided."""
    assert set(get_args(EvidenceKind)) == set(get_args(EpistemicClass)) == {
        "fact",
        "claim",
        "estimate",
        "inference",
        "hypothesis",
        "assumption",
        "unknown",
    }
