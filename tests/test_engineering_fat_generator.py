from nexus_core.engineering_fat_generator import FATRequirement, build_fat


def req(**overrides):
    base = dict(
        requirement_id="PRESSURE",
        project_id="PRJ-HYD-01",
        parameter="test pressure",
        canonical_value="120 MPa",
        evidence_class="FACT",
        source_refs=("MASTER-HYD-v1.1",),
        measurement_method="calibrated pressure transducer",
        acceptance_criterion="reaches and holds canonical pressure without leakage",
        witness_evidence="timestamped pressure trace + FAT witness signoff",
    )
    base.update(overrides)
    return FATRequirement(**base)


def test_ready_requirement_builds_measurement_bound_case():
    result = build_fat("PRJ-HYD-01", [req()])
    assert result.status == "READY"
    assert result.cases[0].expected_value == "120 MPa"
    assert result.cases[0].source_refs == ("MASTER-HYD-v1.1",)


def test_supplier_claim_cannot_become_fat_authority():
    result = build_fat("PRJ-HYD-01", [req(evidence_class="CLAIM", source_refs=("supplier-proposal",))])
    assert result.status == "MISSING_EVIDENCE"
    assert "FACT or MEASUREMENT" in " ".join(result.reasons)


def test_cross_project_requirement_fails_closed():
    result = build_fat("PRJ-HYD-01", [req(project_id="PRJ-CAN-01")])
    assert result.status == "OUT_OF_SCOPE"
    assert result.cases == ()


def test_duplicate_requirement_id_is_conflict():
    result = build_fat("PRJ-HYD-01", [req(), req(parameter="pressure repeatability")])
    assert result.status == "CONFLICT"


def test_partial_ready_set_preserves_valid_cases_but_holds_package():
    weak = req(
        requirement_id="CYCLE_RATE",
        parameter="cycle rate",
        canonical_value="unknown",
        evidence_class="UNKNOWN",
        source_refs=(),
        measurement_method="cycle counter",
        acceptance_criterion="must match canonical requirement",
        witness_evidence="timestamped cycle log",
    )
    result = build_fat("PRJ-HYD-01", [req(), weak])
    assert result.status == "MISSING_EVIDENCE"
    assert len(result.cases) == 1
