from nexus_control_plane.forge_preflight import (
    ForgePreflightRequest,
    PreflightDecision,
    evaluate_registered_forge_preflight,
)
from nexus_control_plane.forge_registry import (
    CANONICAL_OWNERS,
    canonical_owner,
    validate_canonical_owner_registry,
)


def _request(**changes):
    data = dict(
        change_id="change-registry-1",
        concern="forge_lifecycle",
        proposed_owner="PR36",
        evidence_refs=("github:PR36", "github:PR30"),
        runtime_sensitive=False,
        live_verified=False,
        prior_failure_refs=(),
        prior_failures_consulted=False,
        current_content=None,
        proposed_content=None,
    )
    data.update(changes)
    return ForgePreflightRequest(**data)


def test_canonical_registry_is_valid_and_contains_project_wide_core_owners():
    assert validate_canonical_owner_registry() == ()
    assert canonical_owner("evaluation") == "PR6"
    assert canonical_owner("evolution") == "PR19"
    assert canonical_owner("forge_lifecycle") == "PR36"
    assert canonical_owner("exact_external_approval") == "PR37"
    assert len(CANONICAL_OWNERS) >= 10


def test_registered_preflight_blocks_competing_owner_without_callsite_supplied_mapping():
    result = evaluate_registered_forge_preflight(
        _request(concern="evaluation", proposed_owner="PR999")
    )
    assert result.decision is PreflightDecision.BLOCK
    assert any("canonical owner conflict" in blocker for blocker in result.blockers)
    assert result.execution_authorized is False


def test_registered_preflight_holds_unknown_concern_instead_of_implicitly_claiming_it():
    result = evaluate_registered_forge_preflight(
        _request(concern="new_unregistered_framework", proposed_owner="PR999")
    )
    assert result.decision is PreflightDecision.HOLD
    assert any("no canonical owner" in warning for warning in result.warnings)
    assert result.execution_authorized is False


def test_registered_preflight_allows_only_shadow_for_exact_owner_with_clean_evidence():
    result = evaluate_registered_forge_preflight(_request())
    assert result.decision is PreflightDecision.SHADOW_READY
    assert result.blockers == ()
    assert result.warnings == ()
    assert result.execution_authorized is False


def test_registered_preflight_replays_known_failure_and_runtime_guards():
    stale = evaluate_registered_forge_preflight(
        _request(runtime_sensitive=True, live_verified=False)
    )
    assert stale.decision is PreflightDecision.HOLD

    ignored_failure = evaluate_registered_forge_preflight(
        _request(prior_failure_refs=("lesson:supabase-default-grant-drift",))
    )
    assert ignored_failure.decision is PreflightDecision.HOLD

    consulted = evaluate_registered_forge_preflight(
        _request(
            runtime_sensitive=True,
            live_verified=True,
            prior_failure_refs=("lesson:supabase-default-grant-drift",),
            prior_failures_consulted=True,
        )
    )
    assert consulted.decision is PreflightDecision.SHADOW_READY


def test_registered_preflight_blocks_observed_noop_write_recurrence():
    result = evaluate_registered_forge_preflight(
        _request(current_content="same\n", proposed_content="same\n")
    )
    assert result.decision is PreflightDecision.BLOCK
    assert "byte-identical/no-op write blocked" in result.blockers
