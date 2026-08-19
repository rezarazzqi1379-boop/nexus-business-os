import pytest

from nexus_core.continuity import ContinuityPacket, build_resume_instruction, validate_continuity_packet


def packet(**overrides):
    values = dict(
        packet_id="continuity:2026-08-19:1",
        created_at="2026-08-19T21:00:00+03:30",
        source_version_ref="github:pr13:head",
        operating_contract_ref="notion:maximum-mode-v2-1",
        goal_portfolio_ref="notion:goal-portfolio:live",
        active_work_refs=("github:pr:13", "github:pr:9"),
        blocker_refs=("engineering:hydrotester:120mpa-scope",),
        evidence_refs=("gmail:thread:hydrotester", "github:actions:latest"),
        human_gate_refs=("gate:external-send", "gate:merge-deploy"),
        next_resume_instruction="Prioritize live commercial blockers, then code hardening and measured learning outcomes.",
    )
    values.update(overrides)
    return ContinuityPacket(**values)


def test_valid_packet_builds_portable_resume_instruction():
    text = build_resume_instruction(packet())
    assert "canonical continuity input" in text
    assert "not authorization" in text
    assert "live-verify" in text
    assert "current verified evidence win" in text
    assert "do not create a replacement registry" in text.lower()
    assert "highest-value reversible internal work" in text
    assert "human approval" in text


def test_bootstrap_requires_conflict_preservation_instead_of_silent_reconciliation():
    text = build_resume_instruction(packet())
    assert "preserve both refs" in text
    assert "mark the old state stale" in text
    assert "never silently merge contradictory state" in text


def test_bootstrap_routes_every_goal_and_demands_measurable_outcomes():
    text = build_resume_instruction(packet())
    assert "next_action, waiting_blocked, scheduled_review or explicit_pause" in text
    assert "measurable success/failure signals" in text


def test_missing_evidence_fails_closed():
    errors = validate_continuity_packet(packet(evidence_refs=()))
    assert "evidence_refs requires at least one retrievable reference" in errors


def test_naive_timestamp_is_rejected():
    errors = validate_continuity_packet(packet(created_at="2026-08-19T21:00:00"))
    assert "created_at must include a timezone offset" in errors


def test_duplicate_refs_are_rejected():
    errors = validate_continuity_packet(packet(active_work_refs=("github:pr:13", "github:pr:13")))
    assert "active_work_refs cannot contain duplicates" in errors


def test_unicode_formatting_in_packet_id_is_rejected():
    errors = validate_continuity_packet(packet(packet_id="continuity:\u202e1"))
    assert "packet_id cannot contain control or formatting characters" in errors


def test_invalid_packet_never_builds_resume_instruction():
    with pytest.raises(ValueError):
        build_resume_instruction(packet(evidence_refs=()))
