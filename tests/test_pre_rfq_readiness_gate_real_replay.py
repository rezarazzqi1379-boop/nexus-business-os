from nexus_verticals.pre_rfq_readiness_gate import (
    ReadinessDimension,
    ReadinessUnknown,
    assess_pre_rfq_readiness,
)


def test_hydrotester_pipe_end_condition_would_be_blocking_if_known_pre_outreach():
    result = assess_pre_rfq_readiness((
        ReadinessUnknown(
            key="pipe_end_condition",
            dimension=ReadinessDimension.TECHNICAL_BOUNDARY,
            decision_critical=True,
            evidence_ref="gmail:1a027e0f8091a009",
        ),
    ))
    assert result.ready_for_outreach is False
    assert result.blocking_keys == ("pipe_end_condition",)


def test_can_forming_scope_boundary_would_be_blocking_if_known_pre_outreach():
    result = assess_pre_rfq_readiness((
        ReadinessUnknown(
            key="requested_scope_complete_line_vs_end_forming_module",
            dimension=ReadinessDimension.SCOPE_BOUNDARY,
            decision_critical=True,
            evidence_ref="gmail:1a01e603db04f3d9",
        ),
    ))
    assert result.ready_for_outreach is False


def test_kcl_import_permit_would_be_blocking_if_known_pre_outreach():
    result = assess_pre_rfq_readiness((
        ReadinessUnknown(
            key="kcl_import_permit_status",
            dimension=ReadinessDimension.REGULATORY_COMMERCIAL,
            decision_critical=True,
            evidence_ref="gmail:1a01dfe6f78ea7f1",
        ),
    ))
    assert result.ready_for_outreach is False


def test_noncritical_unknown_is_disclosed_without_overblocking():
    result = assess_pre_rfq_readiness((
        ReadinessUnknown(
            key="optional_vendor_reference_format",
            dimension=ReadinessDimension.OTHER,
            decision_critical=False,
            evidence_ref="test:noncritical",
        ),
    ))
    assert result.ready_for_outreach is True
    assert result.blocking_keys == ()
    assert result.disclosed_noncritical_keys == ("optional_vendor_reference_format",)
