from nexus_control_plane.forge_preflight import ForgePreflightRequest, PreflightDecision
from nexus_control_plane.project_preflight import ProjectPreflightRequest, evaluate_project_preflight
from nexus_control_plane.source_authority import AuthorityTier, SourceRecord


def src(**overrides):
    data = dict(
        source_id="PRJ-HYD-01-ENG",
        project_id="PRJ-HYD-01",
        version="1.0",
        status="CANONICAL",
        tier=AuthorityTier.A_CANONICAL,
        authority_scope="hydrostatic tester engineering qualification",
        effective_date="2026-08-23",
    )
    data.update(overrides)
    return SourceRecord(**data)


def forge():
    return ForgePreflightRequest(
        change_id="change:hydrotester-authority-v1",
        concern="hydrotester_authority",
        proposed_owner="PR29",
        evidence_refs=("PRJ-HYD-01-ENG",),
    )


def test_canonical_project_change_can_reach_shadow_ready():
    result = evaluate_project_preflight(ProjectPreflightRequest(forge(), "PRJ-HYD-01", (src(),), True, True))
    assert result.decision is PreflightDecision.SHADOW_READY
    assert result.execution_authorized is False


def test_supplier_claim_cannot_change_stable_requirement():
    supplier = src(
        source_id="supplier-quote",
        status="EVIDENCE",
        tier=AuthorityTier.D_RESEARCH_CLAIM,
    )
    result = evaluate_project_preflight(ProjectPreflightRequest(forge(), "PRJ-HYD-01", (supplier,), True, True))
    assert result.decision is PreflightDecision.BLOCK
    assert any("non-authoritative" in item for item in result.blockers)


def test_fresh_live_dynamic_fact_is_not_enough_for_stable_requirement_change():
    live = src(
        source_id="gmail-latest",
        status="LIVE",
        tier=AuthorityTier.B_LIVE_EVIDENCE,
        dynamic=True,
        fresh=True,
    )
    result = evaluate_project_preflight(ProjectPreflightRequest(forge(), "PRJ-HYD-01", (live,), True, True))
    assert result.decision is PreflightDecision.BLOCK
    assert "Tier A" in result.blockers[0]


def test_fresh_live_dynamic_fact_can_support_dynamic_work():
    live = src(
        source_id="gmail-latest",
        status="LIVE",
        tier=AuthorityTier.B_LIVE_EVIDENCE,
        dynamic=True,
        fresh=True,
    )
    result = evaluate_project_preflight(ProjectPreflightRequest(forge(), "PRJ-HYD-01", (live,), False, True))
    assert result.decision is PreflightDecision.SHADOW_READY


def test_stale_live_dynamic_fact_holds_for_refresh():
    stale = src(
        source_id="gmail-old",
        status="LIVE",
        tier=AuthorityTier.B_LIVE_EVIDENCE,
        dynamic=True,
        fresh=False,
    )
    result = evaluate_project_preflight(ProjectPreflightRequest(forge(), "PRJ-HYD-01", (stale,), False, True))
    assert result.decision is PreflightDecision.HOLD


def test_two_canonical_candidates_block():
    result = evaluate_project_preflight(
        ProjectPreflightRequest(
            forge(),
            "PRJ-HYD-01",
            (src(), src(source_id="PRJ-HYD-01-ENG-COPY", version="copy")),
            True,
            True,
        )
    )
    assert result.decision is PreflightDecision.BLOCK


def test_cross_project_master_is_blocked():
    wrong = src(source_id="PRJ-HTL-01-ENG", project_id="PRJ-HTL-01")
    result = evaluate_project_preflight(ProjectPreflightRequest(forge(), "PRJ-HYD-01", (wrong,), True, True))
    assert result.decision is PreflightDecision.BLOCK
