from dataclasses import replace
from pathlib import Path

import pytest

from owner_decision_runtime import (DelegationMandate, DecisionOption, decide_for_owner,
                                    options_for_portfolio, record_decision_cycle)
from projects import PROJECTS
from unified_data_environment import UnifiedDataHub


def option(action="research", **changes):
    value = DecisionOption("d1", "P1", action, "test choice", ("evidence:1",), 5, 4, 3, 1, True)
    return replace(value, **changes)


def mandate():
    return DelegationMandate("m1", ("P1",), max_risk=2)


def test_selects_safe_reversible_decision_for_owner():
    cycle = decide_for_owner((option(),), mandate())
    assert cycle.results[0].state == "SELECTED"
    assert not cycle.external_actions_executed and not cycle.authority_expanded


@pytest.mark.parametrize("action", ["send", "deploy", "merge", "pay", "create_account"])
def test_consequential_actions_never_inherit_broad_delegation(action):
    cycle = decide_for_owner((option(action, decision_id=f"d-{action}"),), mandate())
    assert cycle.results[0].state == "WAITING_APPROVAL"


def test_risk_cost_irreversibility_and_scope_fail_closed():
    items = (option(decision_id="risk", risk=3), option(decision_id="cost", estimated_cost_microusd=1),
             option(decision_id="irrev", reversible=False), option(decision_id="scope", project_id="P2"))
    cycle = decide_for_owner(items, mandate())
    assert {x.state for x in cycle.results} == {"WAITING_APPROVAL", "DENIED"}


def test_portfolio_has_safe_visible_decision_for_every_project():
    choices = options_for_portfolio(tuple(PROJECTS.values()))
    assert {x.project_id for x in choices} == set(PROJECTS)
    heat = next(x for x in choices if x.project_id == "heat_treatment")
    assert heat.action == "summarize"
    assert "Preserve hold" in heat.objective


def test_cycle_is_persisted_in_existing_hub(tmp_path: Path):
    cycle = decide_for_owner((option(),), mandate())
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    assert record_decision_cycle(hub, cycle, project_id="NEXUS_CORE",
                                 observed_at="2026-09-12T12:00:00+00:00")
    assert hub.project_view("NEXUS_CORE")[0]["category"] == "OWNER_DELEGATED_DECISION"
