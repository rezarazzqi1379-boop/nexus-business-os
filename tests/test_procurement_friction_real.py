import json
from pathlib import Path

from nexus_verticals.pre_rfq_readiness_proposal import proposal_from_friction_pattern
from nexus_verticals.procurement_friction import ProcurementFrictionEvent, mine_procurement_friction_patterns


def _load_real_events():
    raw = json.loads(Path("data/procurement_friction_real_v0_1.json").read_text())
    return tuple(ProcurementFrictionEvent(**row) for row in raw)


def test_three_real_cross_project_friction_events_form_one_eligible_pattern():
    events = _load_real_events()
    assert len(events) == 3
    patterns = mine_procurement_friction_patterns(events)
    assert len(patterns) == 1
    pattern = patterns[0]
    assert pattern.category == "pre_rfq_readiness_gap"
    assert pattern.occurrences == 3
    assert pattern.distinct_projects == 3
    assert pattern.eligible_for_improvement_proposal is True


def test_real_pattern_produces_pr19_compatible_readiness_proposal():
    pattern = mine_procurement_friction_patterns(_load_real_events())[0]
    proposal = proposal_from_friction_pattern(pattern)
    payload = proposal.as_pr19_payload()
    assert set(payload) == {
        "proposal_id",
        "component",
        "hypothesis",
        "change_summary",
        "source_observations",
        "expected_metric",
        "max_regression",
    }
    assert payload["expected_metric"] == "post_outreach_clarification_rework_rate"
    assert len(payload["source_observations"]) == 3
    assert len(proposal.evidence_refs) == 3


def test_two_projects_are_not_enough_for_default_real_pattern_threshold():
    events = _load_real_events()[:2]
    pattern = mine_procurement_friction_patterns(events)[0]
    assert pattern.eligible_for_improvement_proposal is False
