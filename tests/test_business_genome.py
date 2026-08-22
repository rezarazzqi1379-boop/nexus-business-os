from nexus.business_genome import (
    BusinessGenomeRecord,
    Decision,
    Epistemic,
    EvidenceRef,
    NegativeKnowledge,
    OpportunityCandidate,
    ProblemRecord,
    dedupe_genomes,
    rank_opportunities,
)


def ev(kind=Epistemic.FACT):
    return EvidenceRef("source:1", "2026-08-22", kind, "observed evidence", authority=3)


def test_dedupe_keeps_record_with_more_evidence():
    weak = BusinessGenomeRecord("acme", "procurement", "slow RFQ", "faster sourcing", evidence=(ev(),))
    strong = BusinessGenomeRecord("ACME", "Procurement", "slow RFQ", "Faster Sourcing", evidence=(ev(), ev()))
    rows = dedupe_genomes([weak, strong])
    assert len(rows) == 1
    assert len(rows[0].evidence) == 2


def test_high_value_evidence_backed_opportunity_is_pursue():
    problem = ProblemRecord("p1", "manual supplier qualification", ("acme",), 5, 5, 5, 5, (ev(),))
    candidate = OpportunityCandidate(
        "o1", "p1", market=5, access=5, strategic_fit=5, differentiation=4,
        evidence_strength=5, capital=1, complexity=2, competition=2,
        time_to_revenue=1, risk=2, evidence=(ev(),)
    )
    assert candidate.decide(problem) == Decision.PURSUE


def test_weak_evidence_forces_research_even_if_story_is_attractive():
    problem = ProblemRecord("p1", "future need", ("acme",), 5, 5, 5, 5, (ev(Epistemic.HYPOTHESIS),))
    candidate = OpportunityCandidate(
        "o1", "p1", 5, 5, 5, 5, 1, 0, 0, 0, 0, 0,
        evidence=(ev(Epistemic.HYPOTHESIS),)
    )
    assert candidate.decide(problem) == Decision.RESEARCH


def test_missing_problem_is_not_ranked():
    candidate = OpportunityCandidate("o1", "missing", 1, 1, 1, 1, 3, 1, 1, 1, 1, 1, evidence=(ev(),))
    assert rank_opportunities([], [candidate]) == []


def test_negative_knowledge_is_first_class_state():
    nk = NegativeKnowledge()
    nk.duplicate_actions.add("email:vendor:rfq-1")
    nk.invalid_hypotheses.add("supplier-responsive-means-qualified")
    assert "email:vendor:rfq-1" in nk.duplicate_actions
    assert "supplier-responsive-means-qualified" in nk.invalid_hypotheses
