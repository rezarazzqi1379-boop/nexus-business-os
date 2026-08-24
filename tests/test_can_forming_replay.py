from nexus_verticals.can_forming_replay import (
    CanFormingRequirement,
    SupplierQuote,
    assess_quote,
)


def _req(diameter=73, scope="necking_only", cpm=600):
    return CanFormingRequirement(
        requirement_id=f"req-{diameter}-{scope}",
        project_id="can-forming",
        diameter_mm=diameter,
        requested_scope=scope,
        existing_line_cpm=cpm,
        source_ref="file:buyer-engineering-2026-08-17",
    )


def _quote(diameter=73, scope="full_production_line", stable=400, max_cpm=500, claim="claim", sent=True):
    return SupplierQuote(
        quote_id=f"ge-{diameter}",
        supplier="Golden Eagle",
        diameter_mm=diameter,
        quoted_scope=scope,
        price_usd=628200 if diameter == 73 else 636200,
        incoterm="FOB Ningbo",
        max_cpm=max_cpm,
        stable_cpm=stable,
        speed_evidence_class=claim,
        source_ref="file:golden-eagle-quote-2026-08-20",
        clarification_already_sent=sent,
    )


def test_full_production_line_is_not_equivalent_to_necking_only():
    result = assess_quote(_req(scope="necking_only"), _quote())
    assert result.fit_status == "misaligned"
    assert result.scope_conflict is True
    assert any("not equivalent" in blocker for blocker in result.blockers)


def test_full_production_line_is_not_equivalent_to_requested_full_forming_machine_scope():
    result = assess_quote(_req(scope="full_forming"), _quote())
    assert result.fit_status == "misaligned"
    assert result.scope_conflict is True


def test_supplier_speed_claim_never_becomes_verified_through_normalization():
    result = assess_quote(_req(cpm=600), _quote(stable=400, claim="claim"))
    assert result.throughput_verified is False
    assert result.throughput_gap_cpm == 200
    assert any("supplier claim/unverified" in blocker for blocker in result.blockers)


def test_d99_replay_preserves_250_cpm_context_gap_without_auto_rejection_claim():
    result = assess_quote(_req(diameter=99, cpm=650), _quote(diameter=99, stable=400))
    assert result.throughput_gap_cpm == 250
    assert any("required continuous throughput remains unresolved" in blocker for blocker in result.blockers)


def test_existing_line_rating_is_context_not_automatic_acceptance_requirement():
    result = assess_quote(_req(cpm=600), _quote(stable=400))
    assert result.fit_status == "misaligned"
    assert "rejected" not in " ".join(result.blockers).lower()


def test_prior_corrective_clarification_blocks_duplicate_followup_path():
    result = assess_quote(_req(), _quote(sent=True))
    assert result.duplicate_followup_blocked is True


def test_exact_scope_can_align_but_unverified_speed_still_blocks_clean_fit():
    result = assess_quote(_req(scope="necking_only"), _quote(scope="necking_only", stable=600, claim="claim"))
    assert result.scope_conflict is False
    assert result.fit_status == "misaligned"
    assert result.throughput_verified is False


def test_exact_scope_and_verified_speed_can_align():
    result = assess_quote(_req(scope="necking_only"), _quote(scope="necking_only", stable=600, claim="fact", sent=False))
    assert result.fit_status == "aligned"
    assert result.scope_conflict is False
    assert result.throughput_gap_cpm == 0
    assert result.throughput_verified is True
