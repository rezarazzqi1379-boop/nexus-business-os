import pytest

from nexus_core.evidence_authority import AuthorityTaggedHit, resolve_authority_contradiction
from nexus_core.research_data_mesh import ResearchHit


def hit(source_id: str, stance: str, observation: str = "x") -> ResearchHit:
    return ResearchHit("q1", source_id, "claim", "Claim", observation, "strong", 90, stance)


def test_buyer_requirement_outranks_supplier_claim_without_hiding_contradiction():
    result = resolve_authority_contradiction([
        AuthorityTaggedHit(hit("buyer", "refute", "120 MPa required"), "buyer_end_user"),
        AuthorityTaggedHit(hit("supplier", "support", "70 MPa is enough"), "supplier_oem"),
    ])
    assert result.contradiction is True
    assert result.resolution == "refute"
    assert result.refute_authority == 7
    assert result.support_authority == 4
    assert result.decisive_source_ids == ("buyer",)
    assert result.requires_human_review is False


def test_equal_authority_conflict_stays_unresolved_and_requires_review():
    result = resolve_authority_contradiction([
        AuthorityTaggedHit(hit("buyer-email-a", "support"), "buyer_end_user"),
        AuthorityTaggedHit(hit("buyer-email-b", "refute"), "buyer_end_user"),
    ])
    assert result.contradiction is True
    assert result.resolution == "unresolved"
    assert result.requires_human_review is True
    assert result.decisive_source_ids == ("buyer-email-a", "buyer-email-b")


def test_historical_other_project_cannot_override_verified_current_project():
    result = resolve_authority_contradiction([
        AuthorityTaggedHit(hit("current-project", "support"), "verified_project"),
        AuthorityTaggedHit(hit("old-project", "refute"), "historical_other_project"),
    ])
    assert result.resolution == "support"
    assert result.support_authority == 5
    assert result.refute_authority == 2


def test_non_contradictory_claim_keeps_resolution_without_review():
    result = resolve_authority_contradiction([
        AuthorityTaggedHit(hit("approved", "support"), "approved_internal"),
    ])
    assert result.contradiction is False
    assert result.resolution == "support"
    assert result.requires_human_review is False


def test_multiple_claims_fail_closed():
    a = ResearchHit("q1", "a", "claim-a", "A", "x", "strong", 90, "support")
    b = ResearchHit("q1", "b", "claim-b", "B", "y", "strong", 90, "refute")
    with pytest.raises(ValueError, match="authority_resolution_requires_one_claim"):
        resolve_authority_contradiction([
            AuthorityTaggedHit(a, "verified_project"),
            AuthorityTaggedHit(b, "supplier_oem"),
        ])


def test_invalid_runtime_authority_fails_closed():
    bad = AuthorityTaggedHit(hit("a", "support"), "made_up")
    with pytest.raises(ValueError, match="invalid_authority"):
        resolve_authority_contradiction([bad])
