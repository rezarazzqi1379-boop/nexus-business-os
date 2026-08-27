from nexus_core.capability_forge import (
    CapabilityRecord,
    capability_portfolio,
    candidates_for_domain,
    priority_score,
    ranked_improvements,
    should_revisit,
    validate_capabilities,
)


def test_seed_portfolio_is_valid_and_cross_domain():
    records = capability_portfolio()
    assert validate_capabilities(records) == ()
    assert len(records) >= 10
    assert {r.domain for r in records} >= {
        "EXECUTIVE", "COMMERCIAL", "ENGINEERING", "RESEARCH", "CODING",
        "MEMORY", "AUTOMATION", "SECURITY", "DESIGN", "DEPLOYMENT", "COMMUNICATION",
    }


def test_priority_is_deterministic_and_not_authority():
    records = capability_portfolio()
    ranked = ranked_improvements(records)
    assert ranked
    scores = [priority_score(r) for r in ranked]
    assert scores == sorted(scores, reverse=True)
    assert all(r.action in {"BUILD", "BENCHMARK", "CONNECT", "REPAIR"} for r in ranked)


def test_deferred_capability_is_revisitable_not_forgotten():
    temporal = next(r for r in capability_portfolio() if r.capability_id == "CAP-DURABLE-WAIT")
    assert temporal.state == "DEFERRED"
    assert should_revisit(temporal, "repeated-state-loss") is True
    assert should_revisit(temporal, "random-trigger") is False


def test_working_capability_does_not_revisit_by_deferred_trigger():
    item = next(r for r in capability_portfolio() if r.capability_id == "CAP-EXEC-PORTFOLIO")
    assert item.state == "WORKING"
    assert should_revisit(item, "anything") is False


def test_connect_without_candidate_fails_closed():
    bad = CapabilityRecord(
        capability_id="BAD",
        name="Bad",
        domain="AUTOMATION",
        state="GAP",
        action="CONNECT",
        problem="Need adapter",
        current_mechanism="None",
        candidate_refs=(),
        project_refs=("NEXUS_CORE",),
        acceptance_test="Must pass",
        rollback="Remove it",
        frequency=3,
        impact=3,
        safety_risk=3,
        overlap_risk=1,
    )
    assert "CONNECT requires at least one candidate_ref" in bad.validate()


def test_duplicate_capability_id_fails_closed():
    item = capability_portfolio()[0]
    errors = validate_capabilities((item, item))
    assert any("duplicate capability_id" in e for e in errors)


def test_candidate_lookup_is_domain_scoped():
    coding = candidates_for_domain(capability_portfolio(), "CODING")
    assert coding
    assert all(r.domain == "CODING" for r in coding)


def test_no_record_grants_external_or_production_authority():
    # The forge plans internal capability work only. Action vocabulary intentionally has no
    # SEND/MERGE/DEPLOY/PRODUCTION/PAY/SIGN/ORDER/PUBLISH semantics.
    forbidden = {"SEND", "MERGE", "DEPLOY", "PRODUCTION", "PAY", "SIGN", "ORDER", "PUBLISH"}
    assert all(r.action not in forbidden for r in capability_portfolio())


def test_project_specific_engineering_capability_does_not_include_kcl():
    engineering = next(r for r in capability_portfolio() if r.capability_id == "CAP-ENGINEERING-REVIEW")
    assert "PRJ-KCL-01" not in engineering.project_refs
    assert {"PRJ-HYD-01", "PRJ-HTL-01", "PRJ-CAN-01"}.issubset(set(engineering.project_refs))
