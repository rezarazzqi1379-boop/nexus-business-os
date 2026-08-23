from nexus_verticals.productization import (
    ProductizationRecord,
    TenantConfig,
    WorkflowInput,
    WorkflowOutput,
    productization_ready,
)


def atf_config() -> TenantConfig:
    return TenantConfig(
        tenant_id="atf",
        organization_name="ASAK TEJARAT FATER",
        allowed_projects=("hydrotester", "can_forming"),
        required_evidence_classes=("sourced_claim",),
        human_gated_actions=("external_send",),
    )


def hydrotester_record() -> ProductizationRecord:
    return ProductizationRecord(
        config=atf_config(),
        workflow_input=WorkflowInput(
            case_id="hydrotester-rev1-2",
            project_type="hydrotester",
            tenant_id="atf",
            requirement_version="1.2",
            evidence_refs=("buyer-rev1.2", "supplier-quote-gh"),
            evidence_classes=("fact", "sourced_claim"),
            candidate_entities=("GH-Petro",),
            requested_action="internal_analysis",
        ),
        workflow_output=WorkflowOutput(
            case_id="hydrotester-rev1-2",
            decision="modify",
            blockers=("pipe-end condition remains unresolved",),
            next_action="request exact end-condition support before qualification",
            action_mode="internal",
            evidence_refs=("buyer-rev1.2", "supplier-quote-gh"),
        ),
    )


def can_forming_record() -> ProductizationRecord:
    return ProductizationRecord(
        config=atf_config(),
        workflow_input=WorkflowInput(
            case_id="can-forming-d73-d99",
            project_type="can_forming",
            tenant_id="atf",
            requirement_version="scope-v1",
            evidence_refs=("buyer-upgrade-scope", "golden-eagle-material"),
            evidence_classes=("fact", "sourced_claim"),
            candidate_entities=("Golden Eagle",),
            requested_action="internal_analysis",
        ),
        workflow_output=WorkflowOutput(
            case_id="can-forming-d73-d99",
            decision="modify",
            blockers=("quoted full-line scope is not yet equivalent to requested upgrade scope",),
            next_action="normalize necking-only versus full upgrade scope before price comparison",
            action_mode="internal",
            evidence_refs=("buyer-upgrade-scope", "golden-eagle-material"),
        ),
    )


def test_two_distinct_real_workflows_can_share_one_product_contract():
    assert productization_ready((hydrotester_record(), can_forming_record())) is True


def test_single_case_is_not_productization_proof():
    assert productization_ready((hydrotester_record(),)) is False


def test_tenant_project_boundary_fails_closed():
    record = hydrotester_record()
    bad_input = WorkflowInput(
        case_id=record.workflow_input.case_id,
        project_type="kcl",
        tenant_id="atf",
        requirement_version="1",
        evidence_refs=("kcl-source",),
        evidence_classes=("sourced_claim",),
        candidate_entities=("supplier",),
        requested_action="internal_analysis",
    )
    bad = ProductizationRecord(record.config, bad_input, record.workflow_output)
    assert "workflow_input.project_type is not enabled for tenant" in bad.validate()


def test_output_cannot_invent_evidence():
    record = hydrotester_record()
    bad_output = WorkflowOutput(
        case_id=record.workflow_output.case_id,
        decision="modify",
        blockers=("missing proof",),
        next_action="research",
        action_mode="internal",
        evidence_refs=("invented-ref",),
    )
    bad = ProductizationRecord(record.config, record.workflow_input, bad_output)
    assert "workflow_output.evidence_refs must come from workflow input" in bad.validate()


def test_external_send_must_remain_human_gated():
    record = hydrotester_record()
    send_input = WorkflowInput(
        case_id="send-1",
        project_type="hydrotester",
        tenant_id="atf",
        requirement_version="1.2",
        evidence_refs=("buyer-rev1.2",),
        evidence_classes=("sourced_claim",),
        candidate_entities=("GH-Petro",),
        requested_action="external_send",
    )
    unsafe_output = WorkflowOutput(
        case_id="send-1",
        decision="keep",
        blockers=(),
        next_action="send clarification",
        action_mode="internal",
        evidence_refs=("buyer-rev1.2",),
    )
    bad = ProductizationRecord(record.config, send_input, unsafe_output)
    assert "consequential or tenant-gated action must be human_gated" in bad.validate()


def test_modify_requires_explained_blocker():
    record = hydrotester_record()
    bad_output = WorkflowOutput(
        case_id=record.workflow_output.case_id,
        decision="modify",
        blockers=(),
        next_action="research",
        action_mode="internal",
        evidence_refs=record.workflow_output.evidence_refs,
    )
    bad = ProductizationRecord(record.config, record.workflow_input, bad_output)
    assert "modify/reject decision must explain at least one blocker" in bad.validate()
