from nexus_verticals.p0_benchmark import (
    AuthorityLevel,
    AuthorityRecord,
    BenchmarkObservation,
    BenchmarkPairResult,
    can_supersede,
)


def _authority(**overrides):
    values = dict(
        record_id="r1",
        project_id="hydrotester",
        entity_id="machine-spec",
        field_name="pipe_length",
        value="unknown",
        authority_level=AuthorityLevel.A1_BUYER_CONFIRMED,
        source_ref="gmail:buyer-1",
        version=1,
    )
    values.update(overrides)
    return AuthorityRecord(**values)


def test_lower_authority_supplier_claim_cannot_overwrite_buyer_requirement():
    current = _authority(value="6-12m", authority_level=AuthorityLevel.A1_BUYER_CONFIRMED)
    supplier = _authority(
        record_id="r2",
        value="12m",
        authority_level=AuthorityLevel.A5_SUPPLIER_CLAIM,
        source_ref="quote:supplier-1",
        version=2,
    )
    assert can_supersede(current, supplier) is False


def test_other_project_history_cannot_cross_project_boundary():
    hydrotester = _authority(value="unknown")
    heat_treatment = _authority(
        record_id="r2",
        project_id="heat-treatment",
        value="6-12m",
        authority_level=AuthorityLevel.A8_OTHER_PROJECT_HISTORY,
        source_ref="project:heat-treatment",
        version=2,
    )
    assert can_supersede(hydrotester, heat_treatment) is False


def test_stronger_project_specific_record_can_supersede_weaker_claim():
    supplier = _authority(
        value="12m",
        authority_level=AuthorityLevel.A5_SUPPLIER_CLAIM,
        source_ref="quote:supplier-1",
    )
    verified = _authority(
        record_id="r2",
        value="10m",
        authority_level=AuthorityLevel.A3_PROJECT_VERIFIED,
        source_ref="engineering:approved-1",
        version=2,
    )
    assert can_supersede(supplier, verified) is True


def test_same_version_cannot_silently_overwrite():
    current = _authority()
    candidate = _authority(record_id="r2", authority_level=AuthorityLevel.A0_BINDING)
    assert can_supersede(current, candidate) is False


def _obs(case_type, observation_id, accepted):
    return BenchmarkObservation(
        observation_id=observation_id,
        project_id=case_type,
        case_type=case_type,
        stage="measured",
        source_ref=f"benchmark:{observation_id}",
        failure_mode="cross-project contamination" if case_type == "hydrotester" else "scope mismatch",
        metric_name="human_acceptance",
        metric_value=1.0 if accepted else 0.0,
        accepted_by_human=accepted,
    )


def test_benchmark_pair_requires_both_real_case_types():
    pair = BenchmarkPairResult(
        hydrotester=(_obs("hydrotester", "h1", True),),
        can_forming=(_obs("can_forming", "c1", False),),
    )
    assert pair.validate() == []
    assert pair.accepted_precision() == 0.5


def test_benchmark_pair_fails_if_one_case_is_missing():
    pair = BenchmarkPairResult(
        hydrotester=(_obs("hydrotester", "h1", True),),
        can_forming=(),
    )
    assert "can_forming benchmark observations are required" in pair.validate()


def test_no_precision_claim_without_human_decisions():
    undecided = BenchmarkObservation(
        observation_id="h1",
        project_id="hydrotester",
        case_type="hydrotester",
        stage="verified",
        source_ref="benchmark:h1",
        failure_mode="premature supplier qualification",
        metric_name="blocked_invalid_selection",
        metric_value=1,
        accepted_by_human=None,
    )
    pair = BenchmarkPairResult(hydrotester=(undecided,), can_forming=(_obs("can_forming", "c1", True),))
    # Remove the decided observation from the precision denominator by rebuilding the pair.
    pair = BenchmarkPairResult(hydrotester=(undecided,), can_forming=(
        BenchmarkObservation(
            observation_id="c1",
            project_id="can_forming",
            case_type="can_forming",
            stage="verified",
            source_ref="benchmark:c1",
            failure_mode="scope mismatch",
            metric_name="scope_conflict_detected",
            metric_value=1,
            accepted_by_human=None,
        ),
    ))
    assert pair.accepted_precision() is None
