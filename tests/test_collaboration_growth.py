from dataclasses import replace
from pathlib import Path

import pytest

from collaboration_growth import (CollaborationSignal, agent_adaptation_options,
                                  analyze_collaboration, record_growth_report)
from owner_decision_runtime import DelegationMandate, decide_for_owner
from unified_data_environment import UnifiedDataHub


def signal(number=1, **changes):
    value = CollaborationSignal(f"s{number}", "NEXUS_CORE", "REPEATED_INSTRUCTION",
                                "SHARED_PROCESS", 1, 4, .9, (f"task:{number}",),
                                "2026-09-12T14:00:00+03:30")
    return replace(value, **changes)


def test_repeated_evidence_creates_two_sided_support_without_diagnosis():
    report = analyze_collaboration((signal(1), signal(2)), project_id="NEXUS_CORE")
    item = report.recommendations[0]
    assert "contract" in item.agent_adaptation
    assert item.owner_action_optional
    assert not item.diagnosis_made
    assert not report.raw_conversation_stored and not report.sensitive_profile_created


def test_single_observation_cannot_become_a_weakness_claim():
    report = analyze_collaboration((signal(),), project_id="NEXUS_CORE")
    assert report.recommendations == ()


def test_unsupported_sensitive_or_cross_project_signal_fails_closed():
    with pytest.raises(ValueError, match="unsupported"):
        analyze_collaboration((signal(kind="PERSONALITY"),), project_id="NEXUS_CORE")
    with pytest.raises(ValueError, match="cross_project"):
        analyze_collaboration((signal(project_id="OTHER", occurrence_count=2),), project_id="NEXUS_CORE")


def test_agent_adaptation_integrates_with_bounded_decision_engine():
    report = analyze_collaboration((signal(occurrence_count=2),), project_id="NEXUS_CORE")
    options = agent_adaptation_options(report)
    cycle = decide_for_owner(options, DelegationMandate("growth", ("NEXUS_CORE",)))
    assert cycle.results[0].state == "SELECTED"
    assert not cycle.external_actions_executed


def test_growth_summary_persists_without_raw_chat(tmp_path: Path):
    report = analyze_collaboration((signal(occurrence_count=2),), project_id="NEXUS_CORE")
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    assert record_growth_report(hub, report, observed_at="2026-09-12T14:00:00+03:30")
    row = hub.project_view("NEXUS_CORE")[0]
    assert row["category"] == "COLLABORATION_GROWTH"
    assert "no sensitive profile" in row["statement"]
