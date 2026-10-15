import pytest

from nexus_core.opportunity_radar import OpportunityCandidate, decide, ranked
from nexus_core.temporal_evidence import EvidenceNode, cross_project_safe, resolve_subject_field


def node(eid, project, value, start, *, field="pressure", supersedes=()):
    return EvidenceNode(
        evidence_id=eid,
        project_id=project,
        subject_id="supplier-A",
        field=field,
        value=value,
        epistemic_class="FACT",
        source_ref=f"src:{eid}",
        observed_at=start,
        valid_from=start,
        supersedes=supersedes,
    )


def test_temporal_resolution_preserves_project_boundary():
    nodes = (
        node("hyd-1", "PRJ-HYD-01", "70MPa", "2026-08-20T00:00:00Z"),
        node("can-1", "PRJ-CAN-01", "120MPa", "2026-08-20T00:00:00Z"),
    )
    state, active = resolve_subject_field(nodes, "PRJ-HYD-01", "supplier-A", "pressure", "2026-08-21T00:00:00Z")
    assert state == "CURRENT"
    assert [n.evidence_id for n in active] == ["hyd-1"]
    assert [n.evidence_id for n in cross_project_safe(nodes, "PRJ-CAN-01")] == ["can-1"]


def test_temporal_resolution_detects_conflict_instead_of_guessing():
    nodes = (
        node("a", "PRJ-HYD-01", "70MPa", "2026-08-20T00:00:00Z"),
        node("b", "PRJ-HYD-01", "120MPa", "2026-08-21T00:00:00Z"),
    )
    state, active = resolve_subject_field(nodes, "PRJ-HYD-01", "supplier-A", "pressure", "2026-08-22T00:00:00Z")
    assert state == "CONFLICT"
    assert {n.value for n in active} == {"70MPa", "120MPa"}


def test_explicit_supersession_removes_old_value():
    nodes = (
        node("old", "PRJ-HYD-01", "70MPa", "2026-08-20T00:00:00Z"),
        node("new", "PRJ-HYD-01", "120MPa", "2026-08-21T00:00:00Z", supersedes=("old",)),
    )
    state, active = resolve_subject_field(nodes, "PRJ-HYD-01", "supplier-A", "pressure", "2026-08-22T00:00:00Z")
    assert state == "CURRENT"
    assert [n.evidence_id for n in active] == ["new"]


def opportunity(**overrides):
    data = dict(
        opportunity_id="opp-1",
        title="Installed-base retrofit radar",
        problem="Retrofit demand is discovered too late.",
        evidence_refs=("src-1", "src-2"),
        project_refs=("NEXUS_CORE",),
        expected_value=5,
        evidence_quality=4,
        reversibility=4,
        execution_difficulty=2,
        capital_intensity=1,
        safety_risk=2,
        acceptance_test="Find 10 qualified installed-base signals with retrievable evidence and zero duplicate outreach.",
        rollback="Disable radar and preserve evidence packet only.",
    )
    data.update(overrides)
    return OpportunityCandidate(**data)


def test_high_value_reversible_opportunity_can_experiment():
    assert decide(opportunity()) == "EXPERIMENT"


def test_weak_evidence_cannot_auto_promote():
    assert decide(opportunity(evidence_quality=1)) == "WATCH"


def test_capital_heavy_opportunity_requires_validation():
    assert decide(opportunity(capital_intensity=5)) == "VALIDATE"


def test_duplicate_or_critical_risk_rejects():
    assert decide(opportunity(duplicate_of="opp-old")) == "REJECT"
    assert decide(opportunity(safety_risk=5)) == "REJECT"


def test_ranked_rejects_duplicate_ids():
    with pytest.raises(ValueError, match="duplicate opportunity_id"):
        ranked((opportunity(), opportunity()))
