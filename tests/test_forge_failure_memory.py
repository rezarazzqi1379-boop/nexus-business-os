from nexus_control_plane.forge_failure_memory import (
    FAILURE_PATTERNS,
    relevant_failure_refs,
    relevant_failures,
    validate_failure_memory,
)
from nexus_control_plane.forge_preflight import (
    ForgePreflightRequest,
    PreflightDecision,
    evaluate_registered_forge_preflight,
    hydrate_preflight_with_failure_memory,
)


def _request(concern: str, owner: str, **overrides):
    values = dict(
        change_id="change:test",
        concern=concern,
        proposed_owner=owner,
        evidence_refs=("evidence:test",),
        runtime_sensitive=False,
        live_verified=False,
    )
    values.update(overrides)
    return ForgePreflightRequest(**values)


def test_failure_memory_registry_is_valid_and_nontrivial():
    assert validate_failure_memory() == ()
    assert len(FAILURE_PATTERNS) >= 18
    assert len({p.failure_id for p in FAILURE_PATTERNS}) == len(FAILURE_PATTERNS)


def test_evaluation_concern_retrieves_known_failure_classes():
    refs = relevant_failure_refs("evaluation")
    assert "F011_OUTCOME_PROXY_CONFUSION" in refs
    assert "F012_MATURITY_INFLATION_FALSE_COMPLETION" in refs
    assert "F015_UNCALIBRATED_SCORE_PRECISION" in refs
    assert "F016_LLM_JUDGE_OVERTRUST" in refs


def test_security_concern_retrieves_prompt_injection_and_approval_lessons():
    refs = relevant_failure_refs("security_policy_threat_model")
    assert "F006_HARDENING_RECURRENCE" in refs
    assert "F007_APPROVAL_SCOPE_LEAK" in refs
    assert "F017_PROMPT_INJECTION_TOOL_POISONING" in refs


def test_hydration_turns_stored_memory_into_an_actual_read_step():
    request = _request("evaluation", "PR6")
    hydrated = hydrate_preflight_with_failure_memory(request)
    assert hydrated.prior_failure_refs
    assert hydrated.prior_failures_consulted is True
    assert "F016_LLM_JUDGE_OVERTRUST" in hydrated.prior_failure_refs


def test_registered_preflight_uses_internal_memory_without_manual_failure_refs():
    result = evaluate_registered_forge_preflight(_request("evaluation", "PR6"))
    assert result.decision is PreflightDecision.SHADOW_READY
    assert result.execution_authorized is False


def test_caller_supplied_failure_refs_are_not_falsely_marked_consulted():
    request = _request(
        "evaluation",
        "PR6",
        prior_failure_refs=("caller:incident-1",),
        prior_failures_consulted=False,
    )
    hydrated = hydrate_preflight_with_failure_memory(request)
    assert hydrated == request
    result = evaluate_registered_forge_preflight(request)
    assert result.decision is PreflightDecision.HOLD
    assert "relevant prior failures exist but have not been consulted" in result.warnings


def test_unknown_concern_has_no_invented_memory():
    assert relevant_failures("unknown_new_concern") == ()
    request = _request("unknown_new_concern", "PR999")
    hydrated = hydrate_preflight_with_failure_memory(request)
    assert hydrated.prior_failure_refs == ()
    assert hydrated.prior_failures_consulted is False
