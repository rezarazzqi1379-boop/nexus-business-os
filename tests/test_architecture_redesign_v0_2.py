import pytest

from nexus_control_plane.architecture_selector import (
    AgentArchitecture,
    ArchitectureSelectionInput,
    select_agent_architecture,
)
from nexus_control_plane.verification_policy import (
    VerificationMode,
    VerificationRequest,
    build_verification_plan,
)
from nexus_control_plane.verified_state import (
    StateTransitionDecision,
    StateTransitionRequest,
    evaluate_state_transition,
)


def test_sequential_work_defaults_to_single_agent():
    out = select_agent_architecture(
        ArchitectureSelectionInput(0.4, 0.8, 5, 0.3, True)
    )
    assert out.architecture is AgentArchitecture.SINGLE_AGENT
    assert out.max_workers == 1


def test_tool_heavy_moderately_parallel_work_stays_single_agent():
    out = select_agent_architecture(
        ArchitectureSelectionInput(0.65, 0.2, 18, 0.4, True)
    )
    assert out.architecture is AgentArchitecture.SINGLE_AGENT


def test_parallel_research_requires_verification():
    no_verifier = select_agent_architecture(
        ArchitectureSelectionInput(0.9, 0.1, 5, 0.7, False)
    )
    assert no_verifier.architecture is AgentArchitecture.SINGLE_AGENT

    verified = select_agent_architecture(
        ArchitectureSelectionInput(0.9, 0.1, 5, 0.7, True, latency_priority=0.9, cost_priority=0.2)
    )
    assert verified.architecture is AgentArchitecture.PARALLEL_RESEARCH
    assert verified.max_workers == 4


def test_centralized_multi_agent_only_under_degraded_context_and_verification():
    out = select_agent_architecture(
        ArchitectureSelectionInput(0.7, 0.3, 6, 0.8, True)
    )
    assert out.architecture is AgentArchitecture.CENTRALIZED_MULTI_AGENT
    assert out.max_workers == 3


def test_invalid_architecture_inputs_fail_closed():
    with pytest.raises(ValueError):
        select_agent_architecture(ArchitectureSelectionInput(1.2, 0.1, 2, 0.1, True))
    with pytest.raises(ValueError):
        select_agent_architecture(ArchitectureSelectionInput(0.2, 0.1, -1, 0.1, True))


def test_deterministic_verification_outranks_llm_judge():
    plan = build_verification_plan(
        VerificationRequest(False, True, True, False, 0.7)
    )
    assert plan.primary is VerificationMode.DETERMINISTIC
    assert plan.llm_judge_is_authority is False
    assert plan.allow_commit is True


def test_consequential_action_cannot_auto_commit_even_with_deterministic_check():
    plan = build_verification_plan(
        VerificationRequest(True, True, True, True, 0.1)
    )
    assert VerificationMode.HUMAN_REVIEW in plan.secondary
    assert plan.allow_commit is False


def test_llm_only_verification_is_advisory_and_cannot_commit():
    plan = build_verification_plan(
        VerificationRequest(False, False, False, False, 0.8)
    )
    assert plan.primary is VerificationMode.ADVISORY_LLM
    assert plan.llm_judge_is_authority is False
    assert plan.allow_commit is False


def test_state_commit_requires_verifier_and_evidence():
    req = StateTransitionRequest(
        "tx-1", "state:a", "state:b", ("evidence:1",), False
    )
    assert evaluate_state_transition(req).decision is StateTransitionDecision.HOLD


def test_state_transition_that_invalidates_verified_state_holds_for_review():
    req = StateTransitionRequest(
        "tx-2", "state:a", "state:b", ("evidence:1",), True, invalidates_prior_verified_state=True
    )
    out = evaluate_state_transition(req)
    assert out.decision is StateTransitionDecision.HOLD


def test_consequential_state_transition_requires_human_gate():
    req = StateTransitionRequest(
        "tx-3", "state:a", "state:b", ("evidence:1",), True, consequential=True
    )
    assert evaluate_state_transition(req).decision is StateTransitionDecision.HOLD


def test_verified_nonconsequential_state_transition_commits():
    req = StateTransitionRequest(
        "tx-4", "state:a", "state:b", ("evidence:1",), True
    )
    assert evaluate_state_transition(req).decision is StateTransitionDecision.COMMIT
