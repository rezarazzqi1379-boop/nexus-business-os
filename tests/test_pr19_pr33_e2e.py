from nexus.agent_evolution import EvaluationResult, EvolutionProposal, decide_evolution
from nexus_verticals.business_genome_learning import NegativeKnowledgeEvent
from nexus_verticals.pattern_miner import mine_failure_patterns
from nexus_verticals.pattern_to_improvement import proposal_from_pattern


def _eligible_pattern():
    events = (
        NegativeKnowledgeEvent(
            event_id="negative:o1:false-positive",
            observation_id="o1",
            project_id="project:alpha",
            category="pursue_false_positive",
            reason="observed unsuccessful pursue",
            source_ref="evidence:alpha",
        ),
        NegativeKnowledgeEvent(
            event_id="negative:o2:false-positive",
            observation_id="o2",
            project_id="project:beta",
            category="pursue_false_positive",
            reason="observed unsuccessful pursue",
            source_ref="evidence:beta",
        ),
    )
    patterns = mine_failure_patterns(events)
    assert len(patterns) == 1
    assert patterns[0].eligible_for_improvement_proposal is True
    return patterns[0]


def _pr19_proposal():
    pattern = _eligible_pattern()
    adapter = proposal_from_pattern(
        pattern,
        component="opportunity_engine",
        hypothesis="Repeated false-positive PURSUE outcomes indicate the decision boundary is too permissive for this failure mode.",
        change_summary="Evaluate a stricter candidate decision boundary against the frozen baseline; do not deploy automatically.",
        expected_metric="false_positive_rate",
        max_regression=0.0,
    )
    payload = adapter.as_pr19_payload()
    return EvolutionProposal(**payload)


def test_e2e_eligible_pattern_can_be_consumed_by_pr19_and_become_promotable_only_with_evidence_and_gain():
    proposal = _pr19_proposal()
    evaluation = EvaluationResult(
        proposal_id=proposal.proposal_id,
        baseline_score=0.70,
        candidate_score=0.74,
        safety_regressions=(),
        evidence_refs=("eval:baseline-vs-candidate:001",),
    )
    decision = decide_evolution(proposal, evaluation, minimum_gain=0.01)
    assert decision.decision == "promotable"
    assert decision.requires_human_approval is True


def test_e2e_safety_regression_forces_reject_even_when_candidate_score_is_higher():
    proposal = _pr19_proposal()
    evaluation = EvaluationResult(
        proposal_id=proposal.proposal_id,
        baseline_score=0.70,
        candidate_score=0.95,
        safety_regressions=("approval_boundary_regression",),
        evidence_refs=("eval:safety:001",),
    )
    decision = decide_evolution(proposal, evaluation, minimum_gain=0.01)
    assert decision.decision == "reject"
    assert decision.requires_human_approval is False


def test_e2e_missing_evaluation_evidence_forces_reject():
    proposal = _pr19_proposal()
    evaluation = EvaluationResult(
        proposal_id=proposal.proposal_id,
        baseline_score=0.70,
        candidate_score=0.80,
        safety_regressions=(),
        evidence_refs=(),
    )
    decision = decide_evolution(proposal, evaluation, minimum_gain=0.01)
    assert decision.decision == "reject"


def test_e2e_weak_gain_remains_experiment_not_promotable():
    proposal = _pr19_proposal()
    evaluation = EvaluationResult(
        proposal_id=proposal.proposal_id,
        baseline_score=0.70,
        candidate_score=0.705,
        safety_regressions=(),
        evidence_refs=("eval:weak-gain:001",),
    )
    decision = decide_evolution(proposal, evaluation, minimum_gain=0.01)
    assert decision.decision == "experiment"
    assert decision.requires_human_approval is False
