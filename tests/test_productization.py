from dataclasses import replace

from nexus_verticals.productization import (
    ProductizationRecord, TenantConfig, WorkflowInput, WorkflowOutput, productization_ready,
)


def atf_config() -> TenantConfig:
    return TenantConfig("atf", "ASAK TEJARAT FATER", ("hydrotester", "can_forming"), ("sourced_claim",), ("external_send",))


def beta_config() -> TenantConfig:
    return TenantConfig("beta", "Synthetic Beta Co", ("hydrotester", "can_forming"), ("sourced_claim",), ("external_send", "export_packet"))


def hydrotester_record(config=None) -> ProductizationRecord:
    config = config or atf_config()
    t = config.tenant_id
    return ProductizationRecord(
        config,
        WorkflowInput(f"{t}::hydrotester-rev1-2", "hydrotester", t, "1.2", (f"{t}::buyer-rev1.2", f"{t}::supplier-quote-gh"), ("fact", "sourced_claim"), ("GH-Petro",), "internal_analysis"),
        WorkflowOutput(f"{t}::hydrotester-rev1-2", "modify", ("pipe-end condition remains unresolved",), "request exact end-condition support before qualification", "internal", (f"{t}::buyer-rev1.2", f"{t}::supplier-quote-gh")),
    )


def can_forming_record(config=None) -> ProductizationRecord:
    config = config or atf_config()
    t = config.tenant_id
    return ProductizationRecord(
        config,
        WorkflowInput(f"{t}::can-forming-d73-d99", "can_forming", t, "scope-v1", (f"{t}::buyer-upgrade-scope", f"{t}::golden-eagle-material"), ("fact", "sourced_claim"), ("Golden Eagle",), "internal_analysis"),
        WorkflowOutput(f"{t}::can-forming-d73-d99", "modify", ("quoted full-line scope is not yet equivalent to requested upgrade scope",), "normalize necking-only versus full upgrade scope before price comparison", "internal", (f"{t}::buyer-upgrade-scope", f"{t}::golden-eagle-material")),
    )


def test_two_distinct_real_workflows_can_share_one_product_contract():
    assert productization_ready((hydrotester_record(), can_forming_record())) is True


def test_single_case_is_not_productization_proof():
    assert productization_ready((hydrotester_record(),)) is False


def test_tenant_identity_mismatch_fails_closed():
    record = hydrotester_record()
    bad = ProductizationRecord(record.config, replace(record.workflow_input, tenant_id="beta"), record.workflow_output)
    assert "workflow_input.tenant_id must match config.tenant_id" in bad.validate()


def test_project_authorization_bleed_fails_closed():
    record = hydrotester_record()
    bad = ProductizationRecord(record.config, replace(record.workflow_input, project_type="kcl"), record.workflow_output)
    assert "workflow_input.project_type is not enabled for tenant" in bad.validate()


def test_cross_tenant_evidence_isolation_fails_closed():
    record = hydrotester_record()
    bad_input = replace(record.workflow_input, evidence_refs=("beta::stolen-evidence",))
    bad_output = replace(record.workflow_output, evidence_refs=("beta::stolen-evidence",))
    errors = ProductizationRecord(record.config, bad_input, bad_output).validate()
    assert "workflow_input.evidence_refs must be tenant-scoped" in errors
    assert "workflow_output.evidence_refs must be tenant-scoped" in errors


def test_cross_tenant_case_isolation_fails_closed():
    record = hydrotester_record()
    bad_input = replace(record.workflow_input, case_id="beta::same-case")
    bad_output = replace(record.workflow_output, case_id="beta::same-case")
    errors = ProductizationRecord(record.config, bad_input, bad_output).validate()
    assert "workflow_input.case_id must be tenant-scoped" in errors
    assert "workflow_output.case_id must be tenant-scoped" in errors


def test_cross_tenant_config_substitution_fails_closed():
    record = hydrotester_record()
    errors = ProductizationRecord(beta_config(), record.workflow_input, record.workflow_output).validate()
    assert "workflow_input.tenant_id must match config.tenant_id" in errors
    assert "workflow_input.evidence_refs must be tenant-scoped" in errors


def test_unknown_or_missing_tenant_fails_closed():
    record = hydrotester_record()
    unknown = TenantConfig("", "Unknown", ("hydrotester",), ("sourced_claim",), ())
    errors = ProductizationRecord(unknown, replace(record.workflow_input, tenant_id=""), record.workflow_output).validate()
    assert "config.tenant_id is required" in errors
    assert "workflow_input.tenant_id is required" in errors


def test_human_gate_isolation_uses_selected_tenant_policy():
    record = hydrotester_record(beta_config())
    gated_input = replace(record.workflow_input, requested_action="export_packet")
    unsafe_output = replace(record.workflow_output, action_mode="internal")
    errors = ProductizationRecord(record.config, gated_input, unsafe_output).validate()
    assert "consequential or tenant-gated action must be human_gated" in errors


def test_output_cannot_invent_evidence():
    record = hydrotester_record()
    bad_output = replace(record.workflow_output, evidence_refs=("atf::invented-ref",))
    assert "workflow_output.evidence_refs must come from workflow input" in ProductizationRecord(record.config, record.workflow_input, bad_output).validate()


def test_external_send_must_remain_human_gated():
    record = hydrotester_record()
    send_input = replace(record.workflow_input, requested_action="external_send")
    unsafe_output = replace(record.workflow_output, decision="keep", blockers=(), action_mode="internal")
    assert "consequential or tenant-gated action must be human_gated" in ProductizationRecord(record.config, send_input, unsafe_output).validate()


def test_modify_requires_explained_blocker():
    record = hydrotester_record()
    bad_output = replace(record.workflow_output, blockers=())
    assert "modify/reject decision must explain at least one blocker" in ProductizationRecord(record.config, record.workflow_input, bad_output).validate()


def test_same_shared_core_validates_two_tenants_without_tenant_specific_code_branches():
    atf = (hydrotester_record(atf_config()), can_forming_record(atf_config()))
    beta = (hydrotester_record(beta_config()), can_forming_record(beta_config()))
    assert productization_ready(atf) is True
    assert productization_ready(beta) is True
    assert type(atf[0]) is type(beta[0]) is ProductizationRecord
