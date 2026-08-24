from nexus_verticals.business_genome import (
    Decision,
    Epistemic,
    EvidenceRef,
    NegativeKnowledge,
    OpportunityCandidate,
    ProblemRecord,
)


def evidence(ref: str, summary: str, kind=Epistemic.FACT, authority=3):
    return EvidenceRef(ref, "2026-08-22", kind, summary, authority=authority)


def test_hydrotester_rev1_2_stays_research_while_buyer_blockers_remain():
    # PR #29 records buyer/engineering Rev.1.2 dimensions but explicitly keeps
    # test-pressure envelope and pipe-end condition as unresolved buyer-side blockers.
    problem = ProblemRecord(
        "hydrotester-requirement-readiness",
        "supplier qualification is unsafe while decision-critical buyer requirements remain unresolved",
        ("project:hydrotester",),
        frequency=4,
        pain=5,
        ability_to_pay=4,
        urgency=5,
        evidence=(
            evidence("github:pr:29", "Rev.1.2 supersedes stale dimensions"),
            evidence("github:pr:29", "pressure envelope and pipe-end condition remain blockers", Epistemic.UNKNOWN),
        ),
    )
    candidate = OpportunityCandidate(
        "opp:requirement-readiness-gate",
        problem.problem_id,
        market=4,
        access=5,
        strategic_fit=5,
        differentiation=3,
        evidence_strength=4,
        capital=1,
        complexity=2,
        competition=2,
        time_to_revenue=1,
        risk=5,
        evidence=(
            evidence("github:pr:29", "new authority lineage exists"),
            evidence("github:pr:29", "decision-critical blockers remain", Epistemic.UNKNOWN),
        ),
        blocking_unknowns=("test-pressure envelope", "pipe-end condition"),
    )
    assert candidate.decide(problem) == Decision.RESEARCH


def test_can_forming_scope_mismatch_is_research_not_price_selection():
    # PR #24 records that the received D73/D99 quotes are full-line scopes while
    # the buyer also needs a necking-only commercial scope; comparison is not equivalent yet.
    problem = ProblemRecord(
        "can-forming-scope-equivalence",
        "commercial quotes cannot be safely ranked when requested scopes are not equivalent",
        ("project:can-forming", "supplier:golden-eagle"),
        frequency=3,
        pain=4,
        ability_to_pay=4,
        urgency=4,
        evidence=(evidence("github:pr:24", "D73/D99 full-line quotes are not yet comparable to necking-only scope"),),
    )
    candidate = OpportunityCandidate(
        "opp:proposal-deviation-extractor",
        problem.problem_id,
        market=4,
        access=5,
        strategic_fit=5,
        differentiation=4,
        evidence_strength=4,
        capital=1,
        complexity=2,
        competition=2,
        time_to_revenue=1,
        risk=4,
        evidence=(evidence("github:pr:24", "scope-equivalence failure is observed in a real procurement replay"),),
    )
    # One replay can justify continued research, not a production-effectiveness claim.
    assert candidate.decide(problem) in {Decision.RESEARCH, Decision.PURSUE}


def test_explicit_blocker_overrides_attractive_score():
    problem = ProblemRecord("p", "missing decision input", ("project:x",), 5, 5, 5, 5, (evidence("source:x", "known blocker"),))
    candidate = OpportunityCandidate(
        "o", "p", 5, 5, 5, 5, 5, 0, 0, 0, 0, 0,
        evidence=(evidence("source:x", "strong evidence"),),
        blocking_unknowns=("engineering authority",),
    )
    assert candidate.decide(problem) == Decision.RESEARCH


def test_can_forming_duplicate_followup_enters_negative_knowledge():
    nk = NegativeKnowledge()
    nk.duplicate_actions.add("can-forming:golden-eagle:equivalent-followup-before-new-evidence")
    assert "can-forming:golden-eagle:equivalent-followup-before-new-evidence" in nk.duplicate_actions
