from nexus_control_plane.decision_packet import DecisionPacket, validate_decision_packet


def packet(**overrides):
    data = dict(
        packet_id="dp-hyd-001",
        project_id="PRJ-HYD-01",
        subject="supplier technical qualification",
        canonical_source_refs=("PRJ-HYD-01-ENG",),
        live_evidence_refs=("gmail:thread:latest",),
        claim_refs=("claim:supplier:max120",),
        unknowns=(),
        contradiction_refs=(),
        failure_refs=("failure:cross-project-throughput",),
        decision_ref="decision:hyd:qualification:001",
        outcome_target="qualified supplier with guaranteed pressure-size envelope",
        approval_class="external_consequential",
    )
    data.update(overrides)
    return DecisionPacket(**data)


def test_complete_consequential_packet_is_valid():
    assert validate_decision_packet(packet(), consequential=True) == ()


def test_canonical_source_is_required():
    errors = validate_decision_packet(packet(canonical_source_refs=()), consequential=True)
    assert any("canonical_source_refs" in error for error in errors)


def test_consequential_decision_requires_live_evidence():
    errors = validate_decision_packet(packet(live_evidence_refs=()), consequential=True)
    assert any("live evidence" in error for error in errors)


def test_open_contradiction_blocks_release():
    errors = validate_decision_packet(packet(contradiction_refs=("contra:pressure-envelope",)), consequential=True)
    assert any("contradiction" in error for error in errors)


def test_material_unknown_blocks_consequential_release():
    errors = validate_decision_packet(packet(unknowns=("exact pressure matrix",)), consequential=True)
    assert any("unknowns" in error for error in errors)


def test_wrong_approval_class_blocks_consequential_release():
    errors = validate_decision_packet(packet(approval_class="internal_write"), consequential=True)
    assert any("external_consequential" in error for error in errors)


def test_internal_packet_can_exist_without_live_evidence():
    errors = validate_decision_packet(
        packet(live_evidence_refs=(), approval_class="internal_read"),
        consequential=False,
    )
    assert errors == ()


def test_duplicate_refs_fail_closed():
    errors = validate_decision_packet(
        packet(canonical_source_refs=("PRJ-HYD-01-ENG", "PRJ-HYD-01-ENG")),
        consequential=True,
    )
    assert any("canonical_source_refs" in error for error in errors)
