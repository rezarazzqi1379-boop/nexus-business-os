from dataclasses import dataclass
from typing import Literal


EvidenceClass = Literal[
    "fact",
    "sourced_claim",
    "unsourced_claim",
    "estimate",
    "inference",
    "hypothesis",
    "assumption",
    "unknown",
]
ActionMode = Literal["internal", "human_gated"]
ProductDecision = Literal["keep", "modify", "reject"]


CONSEQUENTIAL_ACTIONS = frozenset(
    {
        "external_send",
        "contract",
        "purchase_order",
        "payment",
        "signature",
        "permission_change",
        "production_deploy",
        "protected_merge",
        "public_publish",
        "destructive_database_change",
    }
)


@dataclass(frozen=True)
class TenantConfig:
    tenant_id: str
    organization_name: str
    allowed_projects: tuple[str, ...]
    required_evidence_classes: tuple[EvidenceClass, ...]
    human_gated_actions: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowInput:
    case_id: str
    project_type: str
    tenant_id: str
    requirement_version: str
    evidence_refs: tuple[str, ...]
    evidence_classes: tuple[EvidenceClass, ...]
    candidate_entities: tuple[str, ...]
    requested_action: str


@dataclass(frozen=True)
class WorkflowOutput:
    case_id: str
    decision: ProductDecision
    blockers: tuple[str, ...]
    next_action: str
    action_mode: ActionMode
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class ProductizationRecord:
    config: TenantConfig
    workflow_input: WorkflowInput
    workflow_output: WorkflowOutput

    def validate(self) -> list[str]:
        errors: list[str] = []

        required_text = (
            ("config.tenant_id", self.config.tenant_id),
            ("config.organization_name", self.config.organization_name),
            ("workflow_input.case_id", self.workflow_input.case_id),
            ("workflow_input.project_type", self.workflow_input.project_type),
            ("workflow_input.tenant_id", self.workflow_input.tenant_id),
            ("workflow_input.requirement_version", self.workflow_input.requirement_version),
            ("workflow_input.requested_action", self.workflow_input.requested_action),
            ("workflow_output.case_id", self.workflow_output.case_id),
            ("workflow_output.next_action", self.workflow_output.next_action),
        )
        for name, value in required_text:
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{name} is required")

        if self.workflow_input.tenant_id != self.config.tenant_id:
            errors.append("workflow_input.tenant_id must match config.tenant_id")

        if self.workflow_output.case_id != self.workflow_input.case_id:
            errors.append("workflow_output.case_id must match workflow_input.case_id")

        if self.workflow_input.project_type not in self.config.allowed_projects:
            errors.append("workflow_input.project_type is not enabled for tenant")

        if not self.workflow_input.evidence_refs:
            errors.append("workflow_input.evidence_refs must not be empty")
        if len(set(self.workflow_input.evidence_refs)) != len(self.workflow_input.evidence_refs):
            errors.append("workflow_input.evidence_refs must be unique")

        if not self.workflow_input.evidence_classes:
            errors.append("workflow_input.evidence_classes must not be empty")
        missing_required = set(self.config.required_evidence_classes) - set(
            self.workflow_input.evidence_classes
        )
        if missing_required:
            errors.append(
                "workflow_input.evidence_classes missing tenant-required classes: "
                + ", ".join(sorted(missing_required))
            )

        if not set(self.workflow_output.evidence_refs).issubset(
            set(self.workflow_input.evidence_refs)
        ):
            errors.append("workflow_output.evidence_refs must come from workflow input")

        must_gate = (
            self.workflow_input.requested_action in CONSEQUENTIAL_ACTIONS
            or self.workflow_input.requested_action in self.config.human_gated_actions
        )
        if must_gate and self.workflow_output.action_mode != "human_gated":
            errors.append("consequential or tenant-gated action must be human_gated")

        if self.workflow_output.decision == "keep" and self.workflow_output.blockers:
            errors.append("keep decision cannot contain blockers")

        if self.workflow_output.decision in {"modify", "reject"} and not self.workflow_output.blockers:
            errors.append("modify/reject decision must explain at least one blocker")

        return errors


def productization_ready(records: tuple[ProductizationRecord, ...]) -> bool:
    """Return True only when at least two distinct project types pass the same contract."""
    if len(records) < 2:
        return False
    if any(record.validate() for record in records):
        return False
    project_types = {record.workflow_input.project_type for record in records}
    tenant_ids = {record.config.tenant_id for record in records}
    return len(project_types) >= 2 and len(tenant_ids) == 1
