from dataclasses import replace

from portfolio_control import canonical_portfolio, portfolio_next_actions, validate_portfolio


def _by_id():
    return {item.project_id: item for item in canonical_portfolio()}


def test_canonical_portfolio_is_valid_and_project_isolated():
    portfolio = canonical_portfolio()
    result = validate_portfolio(portfolio)
    assert result.valid, result.errors
    assert {p.project_id for p in portfolio} == {"PRJ-HYD-01", "PRJ-HTL-01", "PRJ-KCL-01", "PRJ-CAN-01"}
    assert len({(p.project_id, p.canonical_source_id) for p in portfolio}) == 4


def test_required_state_locks_match_master_context_v1_9():
    p = _by_id()
    assert p["PRJ-HYD-01"].state == "ACTIVE_QUALIFICATION"
    assert p["PRJ-HTL-01"].state == "PAUSED_BY_MANAGEMENT"
    assert p["PRJ-KCL-01"].state == "COMMERCIAL_REFRESH_HOLD"
    assert p["PRJ-CAN-01"].state == "ENGINEERING_CLARIFICATION"


def test_paused_heat_treatment_cannot_restart_outreach():
    portfolio = list(canonical_portfolio())
    ht = next(i for i, p in enumerate(portfolio) if p.project_id == "PRJ-HTL-01")
    portfolio[ht] = replace(portfolio[ht], action_class="DRAFT")
    result = validate_portfolio(tuple(portfolio))
    assert not result.valid
    assert any("paused project" in e for e in result.errors)


def test_consequential_actions_are_never_auto_runnable():
    portfolio = list(canonical_portfolio())
    idx = next(i for i, p in enumerate(portfolio) if p.project_id == "PRJ-HYD-01")
    portfolio[idx] = replace(portfolio[idx], action_class="EXTERNAL")
    result = validate_portfolio(tuple(portfolio))
    assert not result.valid
    assert any("cannot be auto-runnable" in e for e in result.errors)


def test_cross_project_substitution_fails_closed():
    portfolio = list(canonical_portfolio())
    idx = next(i for i, p in enumerate(portfolio) if p.project_id == "PRJ-CAN-01")
    portfolio[idx] = replace(portfolio[idx], project_id="PRJ-HYD-01")
    result = validate_portfolio(tuple(portfolio))
    assert not result.valid
    assert any("duplicate project_id" in e or "project set" in e for e in result.errors)


def test_missing_evidence_or_canonical_identity_fails_closed():
    portfolio = list(canonical_portfolio())
    idx = next(i for i, p in enumerate(portfolio) if p.project_id == "PRJ-KCL-01")
    portfolio[idx] = replace(portfolio[idx], evidence_refs=(), canonical_version="")
    result = validate_portfolio(tuple(portfolio))
    assert not result.valid
    assert any("evidence refs required" in e for e in result.errors)
    assert any("canonical source identity/version required" in e for e in result.errors)


def test_every_next_action_is_internal_safe_work_only():
    actions = portfolio_next_actions()
    assert len(actions) == 4
    assert all(p.action_class in {"READ", "RESEARCH", "DRAFT", "TEST"} for p in actions)
    assert all(p.action_class not in {"EXTERNAL", "PRODUCTION"} for p in actions)


def test_kcl_historical_quantity_is_not_promoted_to_current_fact():
    kcl = _by_id()["PRJ-KCL-01"]
    assert "current committed quantity/forecast" in kcl.blocking_unknowns
    assert "1,200" not in kcl.next_action


def test_can_forming_candidate_configuration_is_not_promoted_to_stable_requirement():
    can = _by_id()["PRJ-CAN-01"]
    assert set(can.blocking_unknowns) == {"final geometry", "mandatory operations", "required production rate"}
    assert "GT3B64" not in can.next_action
