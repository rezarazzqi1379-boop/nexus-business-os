"""Kernel tests, including the eight replay scenarios that define ACCEPTANCE."""
import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from steel_kernel import (
    CALC_DEPENDENCIES, PROJECT_ALIASES, PROJECT_ID, EpistemicClass, ExecutionStatus,
    Freshness, TokenClass, capacity_statement, freshness_of, ingest_new_evidence,
    preflight, resolve_scope, route_request,
)

INTAKE = Path(__file__).resolve().parents[1] / ".nexus/expert_foundry/ROLLING_MILL_ENGINEERING_INTAKE.json"
TODAY = date(2026, 9, 21)


def intake():
    return json.loads(INTAKE.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

def test_every_alias_resolves_to_the_steel_project():
    for alias in PROJECT_ALIASES:
        assert resolve_scope(f"question about the {alias}").project_id == PROJECT_ID


def test_foreign_project_alone_does_not_resolve_to_steel():
    s = resolve_scope("what is the hydrotester quotation status?")
    assert s.project_id is None
    assert "PRJ-HYD-01" in s.foreign_projects_mentioned


def test_unidentified_request_does_not_default_to_steel():
    assert resolve_scope("how are things going?").project_id is None


def test_scope_rejects_non_string():
    with pytest.raises(ValueError):
        resolve_scope(None)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Freshness
# ---------------------------------------------------------------------------

def test_stable_subjects_never_expire():
    ancient = TODAY - timedelta(days=4000)
    for s in ("drawing", "measurement", "physics", "nameplate"):
        assert freshness_of(s, ancient, TODAY) is Freshness.STABLE


def test_price_ages_then_goes_stale():
    assert freshness_of("price", TODAY - timedelta(days=3), TODAY) is Freshness.FRESH
    assert freshness_of("price", TODAY - timedelta(days=20), TODAY) is Freshness.AGING
    assert freshness_of("price", TODAY - timedelta(days=60), TODAY) is Freshness.STALE


def test_git_state_is_stale_the_moment_it_is_not_today():
    assert freshness_of("git_state", TODAY, TODAY) is Freshness.FRESH
    assert freshness_of("git_state", TODAY - timedelta(days=1), TODAY) is Freshness.STALE


def test_unknown_subject_fails_loudly_rather_than_assuming_fresh():
    with pytest.raises(ValueError, match="no TTL policy"):
        freshness_of("sunspot_count", TODAY, TODAY)


def test_future_retrieval_date_is_rejected():
    with pytest.raises(ValueError):
        freshness_of("price", TODAY + timedelta(days=1), TODAY)


# ---------------------------------------------------------------------------
# Epistemic and execution classes must not be conflated
# ---------------------------------------------------------------------------

def test_epistemic_and_execution_vocabularies_are_disjoint():
    assert not {e.value for e in EpistemicClass} & {s.value for s in ExecutionStatus}


# ===========================================================================
# THE EIGHT REPLAY SCENARIOS - these define kernel acceptance
# ===========================================================================

def test_replay_1_simple_motor_question_stays_in_T1_with_no_agents():
    r = preflight("what is the ST1 motor rated power on the rolling mill?", "lookup",
                  intake(), today=TODAY)
    assert r.passed
    assert r.route.token_class is TokenClass.T1
    assert "independent_reviewer" not in r.capabilities_to_load
    assert "steel_intelligence_agent" not in r.capabilities_to_load
    assert r.route.needs_live_research is False


def test_replay_2_roll_diameter_change_creates_contradiction_without_deleting():
    v = ingest_new_evidence(
        "roll_diameter", 505.0, "mm", EpistemicClass.MEASUREMENT,
        "new CAD sheet 2026-10-01", existing_value=518.0,
        existing_class=EpistemicClass.MEASUREMENT)
    assert v.accepted_as == "CORRECTION"
    assert v.creates_contradiction is True
    assert v.supersedes_existing is True
    assert "retained in the register" in v.note
    for dependent in ("roll_force", "torque", "power", "bite_limit"):
        assert dependent in v.affected_calculations


def test_replay_2b_a_claim_cannot_silently_displace_a_measurement():
    v = ingest_new_evidence(
        "roll_diameter", 550.0, "mm", EpistemicClass.CLAIM, "engineer recollection",
        existing_value=518.0, existing_class=EpistemicClass.MEASUREMENT)
    assert v.creates_contradiction is True
    assert v.supersedes_existing is False
    assert any("cannot silently displace" in b for b in v.blockers)


def test_replay_2c_different_equipment_is_a_new_record_not_a_correction():
    v = ingest_new_evidence(
        "roll_diameter", 600.0, "mm", EpistemicClass.CLAIM, "ST3 sketch",
        existing_value=518.0, existing_class=EpistemicClass.MEASUREMENT,
        same_equipment=False)
    assert v.accepted_as == "SEPARATE_SUBJECT"
    assert v.supersedes_existing is False
    assert v.creates_contradiction is False


def test_replay_3_market_price_request_blocks_on_stale_data():
    r = preflight("what does ST52 flat sell for? rolling mill economics", "market",
                  intake(), retrieved={"price": TODAY - timedelta(days=90)}, today=TODAY)
    assert "price" in r.stale_subjects
    assert r.passed is False, "a market route must not proceed on stale prices"
    assert r.route.needs_live_research is True


def test_replay_4_capacity_estimate_is_never_stated_as_actual():
    s = capacity_statement(16.5, 24.2, 6.0, measured=False)
    assert "ESTIMATED" in s and "NOT a measured figure" in s
    assert "6 s handling per pass" in s and "never been measured" in s
    assert "Do not plan against this number" in s
    measured = capacity_statement(18.0, 19.0, 6.0, measured=True)
    assert "Measured" in measured and "ESTIMATED" not in measured


def test_replay_5_invention_route_requires_prior_art_and_review():
    r = preflight("new idea for the rolling mill: a self-adjusting guide", "invention",
                  intake(), today=TODAY)
    assert "prior_art_register" in r.capabilities_to_load
    assert "failure_memory" in r.capabilities_to_load
    assert r.route.needs_independent_review is True
    assert "prior art BEFORE" in r.route.note


def test_replay_6_cross_project_contamination_is_blocked():
    r = preflight("compare the rolling mill capacity with the hydrotester project",
                  "lookup", intake(), today=TODAY)
    assert r.passed is False
    assert r.scope.contaminated is True
    assert any("must NOT be blended" in b for b in r.blockers)


def test_replay_7_simple_task_does_not_activate_every_capability():
    r = preflight("what is the barrel length on the rolling mill?", "lookup",
                  intake(), today=TODAY)
    assert len(r.capabilities_to_load) <= 2
    assert r.route.token_class is TokenClass.T1


def test_replay_8_engineer_data_change_publishes_its_blast_radius():
    v = ingest_new_evidence(
        "motor_rpm", 750.0, "rpm", EpistemicClass.MEASUREMENT, "photo:ST2 nameplate",
        existing_value=999.0, existing_class=EpistemicClass.CLAIM)
    assert v.supersedes_existing is True
    assert set(v.affected_calculations) >= {"surface_speed", "capacity", "mass_flow"}
    assert "marked STALE until re-run" in v.note


# ---------------------------------------------------------------------------
# Ingestion guards
# ---------------------------------------------------------------------------

def test_anonymous_evidence_is_rejected():
    v = ingest_new_evidence("roll_diameter", 500.0, "mm", EpistemicClass.MEASUREMENT, "  ")
    assert v.accepted_as == "REJECTED"
    assert any("anonymous" in b for b in v.blockers)


def test_unitless_number_is_rejected():
    v = ingest_new_evidence("roll_diameter", 500.0, "", EpistemicClass.MEASUREMENT, "cad:x")
    assert v.accepted_as == "REJECTED"
    assert any("no unit" in b for b in v.blockers)


def test_agreeing_value_is_corroboration_not_contradiction():
    v = ingest_new_evidence("roll_diameter", 518.0, "mm", EpistemicClass.MEASUREMENT,
                            "second CAD read", existing_value=518.0,
                            existing_class=EpistemicClass.MEASUREMENT)
    assert v.creates_contradiction is False
    assert "corroboration" in v.note


def test_every_dependency_subject_is_routable():
    for subject in CALC_DEPENDENCIES:
        v = ingest_new_evidence(subject, 1.0, "mm", EpistemicClass.MEASUREMENT, "src:x")
        assert v.affected_calculations, f"{subject} must publish its blast radius"


# ---------------------------------------------------------------------------
# Routing / preflight behaviour
# ---------------------------------------------------------------------------

def test_calculation_route_runs_code_not_prose():
    assert "rolling_line_concept" in route_request("calculation").capabilities
    assert "do not reason numerically in prose" in route_request("calculation").note


def test_major_decision_requires_independent_review():
    assert route_request("major_decision").needs_independent_review is True


def test_code_route_requires_a_fetch_first():
    r = route_request("code")
    assert "git_fetch" in r.capabilities and "fetch first" in r.note


def test_unknown_route_fails_closed():
    with pytest.raises(ValueError, match="unknown request kind"):
        route_request("vibes")


def test_preflight_stays_quiet_when_nothing_is_wrong():
    r = preflight("ST1 gearbox ratio on the rolling mill?", "lookup", intake(), today=TODAY)
    assert r.passed and r.surface_to_user is False


def test_preflight_surfaces_itself_when_something_is_wrong():
    r = preflight("rolling mill price check", "market", intake(),
                  retrieved={"price": TODAY - timedelta(days=200)}, today=TODAY)
    assert r.surface_to_user is True


def test_preflight_reports_open_contradictions_as_warnings():
    r = preflight("rolling mill roll diameter?", "lookup", intake(), today=TODAY)
    assert any("open contradictions" in w for w in r.warnings)
