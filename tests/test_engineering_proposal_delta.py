import pytest

from nexus_core.engineering_proposal_delta import ProposalItem, Requirement, acceptance_summary, compare_proposal


def reqs():
    return (
        Requirement("R-PRESSURE", "HYDROTESTER", "v1.1", "max_pressure", "120 MPa"),
        Requirement("R-OD", "HYDROTESTER", "v1.1", "od_range", "89-180 mm"),
    )


def test_supplier_claim_matching_text_stays_unverified():
    deltas = compare_proposal(reqs(), (
        ProposalItem("R-PRESSURE", "HYDROTESTER", "120 MPa", "CLAIM", "proposal:p3"),
        ProposalItem("R-OD", "HYDROTESTER", "89-180 mm", "CLAIM", "proposal:p4"),
    ))
    assert all(d.disposition == "UNVERIFIED" for d in deltas)
    assert acceptance_summary(deltas)["ready_for_acceptance"] is False


def test_verified_measurement_can_match():
    deltas = compare_proposal(reqs(), (
        ProposalItem("R-PRESSURE", "HYDROTESTER", "120 MPa", "MEASUREMENT", "fat:pressure"),
        ProposalItem("R-OD", "HYDROTESTER", "89-180 mm", "FACT", "signed-spec:od"),
    ))
    assert all(d.disposition == "MATCH" for d in deltas)
    assert acceptance_summary(deltas)["ready_for_acceptance"] is True


def test_deviation_and_missing_are_explicit():
    deltas = compare_proposal(reqs(), (
        ProposalItem("R-PRESSURE", "HYDROTESTER", "70 MPa", "FACT", "catalog:p8"),
    ))
    assert deltas[0].disposition == "DEVIATION"
    assert deltas[1].disposition == "MISSING"


def test_cross_project_contamination_fails_closed():
    with pytest.raises(ValueError, match="cross-project"):
        compare_proposal(reqs(), (
            ProposalItem("R-PRESSURE", "CAN-FORMING", "120 MPa", "FACT", "wrong-project"),
        ))


def test_mixed_canonical_versions_fail_closed():
    mixed = (
        Requirement("R1", "HYDROTESTER", "v1.0", "x", "1"),
        Requirement("R2", "HYDROTESTER", "v1.1", "y", "2"),
    )
    with pytest.raises(ValueError, match="canonical version"):
        compare_proposal(mixed, ())
