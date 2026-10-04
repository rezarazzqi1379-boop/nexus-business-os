import pytest

from nexus_control_plane.workforce import (
    ActionClass,
    CapabilitySpec,
    Department,
    EvidenceClass,
    PUBLIC_PATTERN_CAPABILITIES,
    catalog,
    select_capabilities,
)


def test_catalog_has_unique_canonical_ids():
    items = catalog()
    ids = [item.capability_id for item in items]
    assert len(ids) == len(set(ids))
    assert all(item.capability_id == item.capability_id.strip() for item in items)


def test_public_patterns_are_provenance_labeled():
    assert PUBLIC_PATTERN_CAPABILITIES
    assert all(item.evidence_class is EvidenceClass.OBSERVED_PUBLIC for item in PUBLIC_PATTERN_CAPABILITIES)
    assert all(item.source_ref for item in PUBLIC_PATTERN_CAPABILITIES)


def test_external_and_financial_actions_fail_closed_without_human_gate():
    bad = CapabilitySpec(
        capability_id="x.send",
        label="Send",
        department=Department.SALES,
        action_class=ActionClass.EXTERNAL_WRITE,
        evidence_class=EvidenceClass.INFERRED_EQUIVALENT,
        description="unsafe test fixture",
        requires_human_approval=False,
    )
    with pytest.raises(ValueError, match="human approval"):
        bad.validate()


def test_public_observation_requires_source_ref():
    bad = CapabilitySpec(
        capability_id="x.public",
        label="Public Capability",
        department=Department.INTELLIGENCE,
        action_class=ActionClass.RESEARCH,
        evidence_class=EvidenceClass.OBSERVED_PUBLIC,
        description="unsafe test fixture",
    )
    with pytest.raises(ValueError, match="source_ref"):
        bad.validate()


def test_select_capabilities_filters_without_mutating_catalog():
    all_items = catalog()
    intel = select_capabilities(departments=[Department.INTELLIGENCE])
    assert intel
    assert all(item.department is Department.INTELLIGENCE for item in intel)
    assert len(catalog()) == len(all_items)
