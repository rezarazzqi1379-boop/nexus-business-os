import pytest

from nexus_verticals.pattern_miner import PatternCandidate
from nexus_verticals.pattern_proposal_adapter import (
    PR19_CONTRACT_VERSION,
    proposal_from_pattern,
)


def pattern(*, eligible: bool = True, kind: str = "failure") -> PatternCandidate:
    return PatternCandidate(
        pattern_id=f"{kind}:scope_mismatch",
        kind=kind,
        key="scope_mismatch",
        occurrences=2,
        distinct_projects=2,
        observation_ids=("obs:1", "obs:2"),
        source_refs=("gmail:1", "github:pr:24"),
        eligible_for_improvement_proposal=eligible,
        reason="test",
    )


def test_ineligible_pattern_cannot_create_proposal():
    with pytest.raises(ValueError, match="not eligible"):
        proposal_from_pattern(
            pattern(eligible=False),
            proposal_id="proposal:1",
            component="procurement_scope_checker",
            hypothesis="add stricter scope equivalence checks",
            change_summary="block shortlist when vendor scope exceeds buyer request",
            expected_metric="scope_mismatch_false_positive_rate",
        )


def test_proposal_retains_pattern_evidence_and_version():
    proposal = proposal_from_pattern(
        pattern(),
        proposal_id="proposal:scope:1",
        component="procurement_scope_checker",
        hypothesis="stricter scope equivalence reduces false qualification",
        change_summary="add bounded scope-equivalence precheck before shortlist",
        expected_metric="scope_mismatch_false_positive_rate",
        max_regression=0.01,
    )
    assert proposal.pattern_id == "failure:scope_mismatch"
    assert proposal.evidence_refs == ("gmail:1", "github:pr:24")
    assert proposal.source_observations == ("obs:1", "obs:2")
    assert proposal.contract_version == PR19_CONTRACT_VERSION


def test_pr19_payload_is_exact_evolution_proposal_contract():
    proposal = proposal_from_pattern(
        pattern(kind="success"),
        proposal_id="proposal:success:1",
        component="supplier_outreach",
        hypothesis="reuse confirmed high-performing outreach structure",
        change_summary="evaluate candidate outreach template against baseline",
        expected_metric="qualified_reply_rate",
    )
    payload = proposal.as_pr19_payload()
    assert set(payload) == {
        "proposal_id",
        "component",
        "hypothesis",
        "change_summary",
        "source_observations",
        "expected_metric",
        "max_regression",
    }
    assert payload["source_observations"] == ("obs:1", "obs:2")


def test_missing_retrievable_evidence_fails_closed():
    bad = PatternCandidate(
        pattern_id="failure:x",
        kind="failure",
        key="x",
        occurrences=2,
        distinct_projects=2,
        observation_ids=("obs:1", "obs:2"),
        source_refs=(),
        eligible_for_improvement_proposal=True,
        reason="bad fixture",
    )
    with pytest.raises(ValueError, match="retrievable evidence"):
        proposal_from_pattern(
            bad,
            proposal_id="proposal:x",
            component="x",
            hypothesis="x",
            change_summary="x",
            expected_metric="x",
        )
