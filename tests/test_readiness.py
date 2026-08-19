from nexus_verticals.readiness import RequirementInput, assess_requirement_readiness


def test_discovery_can_proceed_with_explicit_unknown_blockers():
    assessment = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range",
                state="approved",
                value="89-180 mm",
                source_ref="engineering:approved:od",
            ),
            RequirementInput(
                requirement_id="hydrotester.max_pressure",
                name="Maximum machine rating",
                state="approved",
                value="120 MPa",
                source_ref="engineering:approved:max-pressure",
            ),
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length range",
                state="unknown_blocking",
            ),
            RequirementInput(
                requirement_id="hydrotester.wall_or_id",
                name="Wall thickness or ID range",
                state="unknown_blocking",
            ),
        ]
    )

    assert assessment.ready_for_discovery is True
    assert assessment.ready_for_final_request is False
    assert assessment.blocking_ids == (
        "hydrotester.length",
        "hydrotester.wall_or_id",
    )
    assert assessment.provisional_ids == ()
    assert assessment.errors == ()


def test_provisional_values_are_visible_and_block_final_request():
    assessment = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length",
                state="provisional",
                value="12 m",
                source_ref="gmail:historical-outbound",
            )
        ]
    )

    assert assessment.ready_for_discovery is True
    assert assessment.ready_for_final_request is False
    assert assessment.provisional_ids == ("hydrotester.length",)
    assert assessment.errors == ()


def test_all_approved_requirements_are_ready_for_final_request():
    assessment = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range",
                state="approved",
                value="89-180 mm",
                source_ref="engineering:approved:od",
            ),
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length range",
                state="approved",
                value="6-12 m",
                source_ref="engineering:approved:length",
            ),
        ]
    )

    assert assessment.ready_for_discovery is True
    assert assessment.ready_for_final_request is True
    assert assessment.blocking_ids == ()
    assert assessment.provisional_ids == ()
    assert assessment.errors == ()


def test_approved_requirement_needs_value_and_source():
    assessment = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length range",
                state="approved",
            )
        ]
    )

    assert assessment.ready_for_discovery is False
    assert assessment.ready_for_final_request is False
    assert "approved requirement hydrotester.length needs a value" in assessment.errors
    assert "approved requirement hydrotester.length needs a source_ref" in assessment.errors


def test_unknown_blocking_cannot_hide_an_authoritative_value():
    assessment = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.length",
                name="Pipe length range",
                state="unknown_blocking",
                value="12 m",
            )
        ]
    )

    assert assessment.ready_for_discovery is False
    assert assessment.ready_for_final_request is False
    assert (
        "unknown_blocking requirement hydrotester.length must not carry an authoritative value"
        in assessment.errors
    )


def test_duplicate_requirement_ids_are_rejected():
    assessment = assess_requirement_readiness(
        [
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range",
                state="approved",
                value="89-180 mm",
                source_ref="engineering:approved:od",
            ),
            RequirementInput(
                requirement_id="hydrotester.od",
                name="Pipe OD range duplicate",
                state="approved",
                value="89-180 mm",
                source_ref="engineering:approved:od",
            ),
        ]
    )

    assert assessment.ready_for_discovery is False
    assert assessment.ready_for_final_request is False
    assert "duplicate requirement_id: hydrotester.od" in assessment.errors
