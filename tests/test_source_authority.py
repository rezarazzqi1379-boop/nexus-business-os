import json
from pathlib import Path

import pytest

from nexus_control_plane.source_authority import (
    AuthorityDecision,
    AuthorityTier,
    SourceRecord,
    assess_source_for_use,
    resolve_same_scope_candidates,
)


def source(**overrides):
    data = dict(
        source_id="PRJ-HYD-01-ENG",
        project_id="PRJ-HYD-01",
        version="1.0",
        status="CANONICAL",
        tier=AuthorityTier.A_CANONICAL,
        authority_scope="hydrostatic tester engineering qualification",
        effective_date="2026-08-23",
    )
    data.update(overrides)
    return SourceRecord(**data)


def test_current_tier_a_is_accepted():
    result = assess_source_for_use(source(), expected_project_id="PRJ-HYD-01", consequential=True)
    assert result.decision is AuthorityDecision.ACCEPT
    assert result.governing_source_id == "PRJ-HYD-01-ENG"


def test_cross_project_source_is_blocked():
    result = assess_source_for_use(source(), expected_project_id="PRJ-HTL-01", consequential=True)
    assert result.decision is AuthorityDecision.BLOCK_CONFLICT


def test_superseded_source_cannot_govern():
    result = assess_source_for_use(source(superseded=True), expected_project_id="PRJ-HYD-01", consequential=True)
    assert result.decision is AuthorityDecision.REJECT_NON_AUTHORITY


def test_research_claim_never_governs():
    result = assess_source_for_use(
        source(source_id="supplier-pdf", tier=AuthorityTier.D_RESEARCH_CLAIM, status="EVIDENCE"),
        expected_project_id="PRJ-HYD-01",
        consequential=True,
    )
    assert result.decision is AuthorityDecision.REJECT_NON_AUTHORITY


def test_stale_dynamic_live_evidence_requires_refresh():
    result = assess_source_for_use(
        source(source_id="gmail-thread", tier=AuthorityTier.B_LIVE_EVIDENCE, status="LIVE", dynamic=True, fresh=False),
        expected_project_id="PRJ-HYD-01",
        consequential=True,
    )
    assert result.decision is AuthorityDecision.HOLD_REFRESH
    assert result.requires_live_refresh is True


def test_fresh_dynamic_live_evidence_can_govern_dynamic_point():
    result = assess_source_for_use(
        source(source_id="gmail-thread", tier=AuthorityTier.B_LIVE_EVIDENCE, status="LIVE", dynamic=True, fresh=True),
        expected_project_id="PRJ-HYD-01",
        consequential=True,
    )
    assert result.decision is AuthorityDecision.ACCEPT


def test_live_evidence_cannot_silently_rewrite_stable_requirement():
    result = assess_source_for_use(
        source(source_id="quote", tier=AuthorityTier.B_LIVE_EVIDENCE, status="LIVE", dynamic=False, fresh=True),
        expected_project_id="PRJ-HYD-01",
        consequential=True,
    )
    assert result.decision is AuthorityDecision.REJECT_NON_AUTHORITY


def test_two_active_tier_a_candidates_block_instead_of_guessing():
    result = resolve_same_scope_candidates(
        (source(), source(source_id="PRJ-HYD-01-ENG-COPY", version="1.0-copy")),
        expected_project_id="PRJ-HYD-01",
        consequential=True,
    )
    assert result.decision is AuthorityDecision.BLOCK_CONFLICT


def test_operational_state_cannot_create_consequential_authority():
    result = assess_source_for_use(
        source(source_id="notion-state", tier=AuthorityTier.C_OPERATIONAL_STATE, status="CURRENT"),
        expected_project_id="PRJ-HYD-01",
        consequential=True,
    )
    assert result.decision is AuthorityDecision.REJECT_NON_AUTHORITY


def test_source_registry_and_project_requirements_are_cross_linked():
    root = Path(__file__).resolve().parents[1]
    source_registry = json.loads((root / "data/canonical_source_registry_v1_0.json").read_text())
    project_registry = json.loads((root / "data/canonical_project_requirements_v1_0.json").read_text())
    canonical_ids = {row["source_id"] for row in source_registry["canonical_sources"]}
    for project_id, project in project_registry["projects"].items():
        assert project["canonical_source_id"] in canonical_ids, project_id
        assert project["confirmed"]
        assert project["unknown_requires_fresh_verification"]


def test_cross_project_throughput_lock_is_preserved_in_registry():
    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "data/canonical_project_requirements_v1_0.json").read_text())
    assert data["projects"]["PRJ-HYD-01"]["confirmed"]["throughput"] == "approximately 60 pipes/hour"
    assert data["projects"]["PRJ-HTL-01"]["confirmed"]["throughput"] == "approximately 40 pipes/hour"


def test_invalid_record_fails_closed():
    with pytest.raises(ValueError):
        source(source_id=" ")
