from nexus_control_plane.forge_preflight import (
    ForgePreflightRequest,
    PreflightDecision,
    evaluate_forge_preflight,
)


OWNERS = {
    "evaluation": "PR6",
    "evolution": "PR19",
    "exact_external_approval": "PR37",
    "forge_lifecycle": "PR36",
}


def _request(**changes):
    data = dict(
        change_id="change-1",
        concern="forge_lifecycle",
        proposed_owner="PR36",
        evidence_refs=("github:PR36",),
        runtime_sensitive=False,
        live_verified=False,
        prior_failure_refs=(),
        prior_failures_consulted=False,
        current_content=None,
        proposed_content=None,
    )
    data.update(changes)
    return ForgePreflightRequest(**data)


def test_existing_canonical_owner_conflict_is_blocked():
    result = evaluate_forge_preflight(
        _request(concern="evaluation", proposed_owner="PR99"),
        canonical_owners=OWNERS,
    )
    assert result.decision is PreflightDecision.BLOCK
    assert any("canonical owner conflict" in blocker for blocker in result.blockers)
    assert result.execution_authorized is False


def test_runtime_sensitive_claim_without_live_verification_is_held():
    result = evaluate_forge_preflight(
        _request(runtime_sensitive=True, live_verified=False),
        canonical_owners=OWNERS,
    )
    assert result.decision is PreflightDecision.HOLD
    assert "runtime-sensitive claim is not live-verified" in result.warnings


def test_prior_failure_must_be_consulted_before_shadow_ready():
    result = evaluate_forge_preflight(
        _request(prior_failure_refs=("lesson:supabase-default-grant-drift",)),
        canonical_owners=OWNERS,
    )
    assert result.decision is PreflightDecision.HOLD
    assert "relevant prior failures exist but have not been consulted" in result.warnings


def test_byte_identical_write_is_blocked_before_mutation():
    result = evaluate_forge_preflight(
        _request(current_content="same\n", proposed_content="same\n"),
        canonical_owners=OWNERS,
    )
    assert result.decision is PreflightDecision.BLOCK
    assert "byte-identical/no-op write blocked" in result.blockers


def test_unknown_concern_requires_consolidation_hold_not_new_framework_by_default():
    result = evaluate_forge_preflight(
        _request(concern="new_magic_framework", proposed_owner="PR999"),
        canonical_owners=OWNERS,
    )
    assert result.decision is PreflightDecision.HOLD
    assert any("no canonical owner" in warning for warning in result.warnings)


def test_clean_request_is_shadow_ready_but_never_execution_authorized():
    result = evaluate_forge_preflight(_request(), canonical_owners=OWNERS)
    assert result.decision is PreflightDecision.SHADOW_READY
    assert result.blockers == ()
    assert result.warnings == ()
    assert result.execution_authorized is False


def test_live_verified_runtime_change_with_consulted_failure_can_reach_shadow():
    result = evaluate_forge_preflight(
        _request(
            runtime_sensitive=True,
            live_verified=True,
            prior_failure_refs=("lesson:supabase-default-grant-drift",),
            prior_failures_consulted=True,
        ),
        canonical_owners=OWNERS,
    )
    assert result.decision is PreflightDecision.SHADOW_READY


def test_malformed_unhashable_evidence_and_concern_fail_closed_without_crash():
    malformed_refs = _request(evidence_refs=("ok", ["bad"]))
    result_refs = evaluate_forge_preflight(malformed_refs, canonical_owners=OWNERS)
    assert result_refs.decision is PreflightDecision.BLOCK

    malformed_concern = _request(concern=["not", "a", "string"])
    result_concern = evaluate_forge_preflight(malformed_concern, canonical_owners=OWNERS)
    assert result_concern.decision is PreflightDecision.BLOCK
