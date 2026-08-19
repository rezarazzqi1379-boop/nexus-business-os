from dataclasses import replace

from nexus_core.commercial_intelligence import CommercialCandidate, forecast_candidate, rank_candidates


def _candidate(**overrides):
    base = CommercialCandidate(
        candidate_id="c1",
        company_name="Example Pipe",
        fit="strong",
        need="strong",
        decision_path="partial",
        contact_path="strong",
        responsiveness="partial",
        technical_readiness="partial",
        commercial_readiness="partial",
        compliance_readiness="partial",
        risk_penalty=0.1,
        evidence_refs=("exa:company", "gmail:thread"),
    )
    return replace(base, **overrides)


def test_unverified_need_blocks_false_opportunity_inflation() -> None:
    forecast = forecast_candidate(_candidate(need="unverified"))
    assert "need not proven" in forecast.blockers
    assert forecast.band != "deal_ready"


def test_missing_evidence_fails_closed() -> None:
    forecast = forecast_candidate(_candidate(evidence_refs=()))
    assert forecast.band == "blocked"
    assert forecast.score == 0.0


def test_high_quality_complete_candidate_reaches_deal_ready() -> None:
    forecast = forecast_candidate(_candidate(
        decision_path="strong",
        responsiveness="strong",
        technical_readiness="strong",
        commercial_readiness="strong",
        compliance_readiness="strong",
        risk_penalty=0.0,
    ))
    assert forecast.band == "deal_ready"
    assert forecast.next_best_action == "prepare Deal Decision Packet"


def test_risk_penalty_can_demote_candidate() -> None:
    clean = forecast_candidate(_candidate(
        decision_path="strong", responsiveness="strong", technical_readiness="strong",
        commercial_readiness="strong", compliance_readiness="strong", risk_penalty=0.0,
    ))
    risky = forecast_candidate(_candidate(
        decision_path="strong", responsiveness="strong", technical_readiness="strong",
        commercial_readiness="strong", compliance_readiness="strong", risk_penalty=1.0,
    ))
    assert risky.score < clean.score
    assert risky.band != "deal_ready"


def test_rank_candidates_prioritizes_stronger_evidence() -> None:
    strong = _candidate(candidate_id="strong", decision_path="strong", responsiveness="strong")
    weak = _candidate(candidate_id="weak", fit="weak", need="weak", contact_path="partial")
    ranked = rank_candidates((weak, strong))
    assert ranked[0].candidate_id == "strong"
