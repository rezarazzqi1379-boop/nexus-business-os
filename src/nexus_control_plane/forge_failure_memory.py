from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class FailureSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FailurePattern:
    failure_id: str
    concerns: tuple[str, ...]
    severity: FailureSeverity
    evidence_refs: tuple[str, ...]
    lesson: str
    required_checks: tuple[str, ...]


_PATTERNS = (
    FailurePattern(
        "F001_STALE_AUTHORITY_SPEC_LEAK",
        ("requirement_readiness", "hydrotester_authority", "business_genome"),
        FailureSeverity.CRITICAL,
        ("NEXUS_Master_Context_v1.2_2026-08-21", "PR29"),
        "Project-specific engineering authority must supersede historical or neighboring-project values; similar dimensions are not transferable evidence.",
        ("resolve_project", "verify_current_authority", "check_supersession"),
    ),
    FailurePattern(
        "F002_CLAIM_TO_FACT_PROMOTION",
        ("evidence_semantics", "business_genome", "decision_outcome_learning"),
        FailureSeverity.CRITICAL,
        ("NEXUS_Master_Context_v1.1_claim_protocol", "PR1"),
        "A supplier, user, model or document statement remains a claim until the required verification level is met.",
        ("preserve_epistemic_class", "seek_disconfirming_evidence", "record_scope_and_freshness"),
    ),
    FailurePattern(
        "F003_ARCHITECTURE_SPRAWL",
        ("forge_lifecycle", "capability_adoption_governor", "cross_project_runtime", "evolution"),
        FailureSeverity.HIGH,
        ("PR30", "PR36"),
        "Do not create a second owner, evaluator, registry or learning engine when a canonical concern already exists.",
        ("canonical_owner_check", "overlap_scan", "extract_instead_of_duplicate"),
    ),
    FailurePattern(
        "F004_SNAPSHOT_INCOMPLETENESS",
        ("forge_lifecycle", "cross_project_runtime", "audit_metadata"),
        FailureSeverity.HIGH,
        ("PR36_run_555", "forge_open_pr_shadow_audit_2026-08-23"),
        "A snapshot can look internally valid while omitting live records; completeness must be checked against an independent inventory count or cursor/exhaustion proof.",
        ("inventory_count_check", "pagination_exhaustion", "coverage_check"),
    ),
    FailurePattern(
        "F005_CONNECTOR_STATE_DRIFT",
        ("cross_project_runtime", "supabase_least_privilege", "capability_action_routing"),
        FailureSeverity.HIGH,
        ("NEXUS_Orchestrator_Audit_Evidence_Pack_v0.1", "PR16"),
        "Connected/degraded/offline is temporal state, not a permanent property; runtime-sensitive claims require live verification.",
        ("live_probe", "record_verified_at", "separate_read_write_migrate_health"),
    ),
    FailurePattern(
        "F006_HARDENING_RECURRENCE",
        ("supabase_least_privilege", "forge_lifecycle", "security_policy_threat_model"),
        FailureSeverity.CRITICAL,
        ("PR16", "NEXUS_Resume_Pack_2026-08-23"),
        "Snapshot hardening is insufficient if future-created objects can recreate the same exposure; verify defaults and recurrence paths.",
        ("future_object_test", "default_privilege_check", "regression_after_schema_growth"),
    ),
    FailurePattern(
        "F007_APPROVAL_SCOPE_LEAK",
        ("exact_external_approval", "capability_action_routing", "security_policy_threat_model"),
        FailureSeverity.CRITICAL,
        ("PR18", "PR37"),
        "Approval must bind one exact consequential action; it must not authorize later follow-ups or changed content, recipients, attachments or source versions.",
        ("exact_action_digest", "fresh_approval_on_change", "followup_not_preapproved"),
    ),
    FailurePattern(
        "F008_RETRYABLE_VS_CONTAINED_STATE",
        ("forge_lifecycle", "capability_action_routing", "cross_project_runtime"),
        FailureSeverity.HIGH,
        ("PR36_run_548", "PR36_run_549"),
        "Temporary dependency blocking and policy containment are different semantics and must not share irreversible routing behavior.",
        ("classify_block_reason", "allow_safe_retry", "preserve_policy_containment"),
    ),
    FailurePattern(
        "F009_NOOP_WRITE_HISTORY_NOISE",
        ("forge_lifecycle", "audit_metadata"),
        FailureSeverity.MEDIUM,
        ("PR36_noop_write_lesson",),
        "Byte-identical writes create misleading activity and history noise; detect no-op mutations before write.",
        ("content_digest_compare", "skip_noop_write"),
    ),
    FailurePattern(
        "F010_OPTIMISTIC_CONCURRENCY",
        ("forge_lifecycle", "audit_metadata", "cross_project_runtime"),
        FailureSeverity.HIGH,
        ("PR36_stale_sha_409",),
        "Mutable state must use current-version preconditions; on conflict, re-read and re-evaluate instead of forcing an overwrite.",
        ("version_precondition", "reread_on_conflict", "no_force_overwrite"),
    ),
    FailurePattern(
        "F011_OUTCOME_PROXY_CONFUSION",
        ("business_genome", "decision_outcome_learning", "evaluation", "evolution"),
        FailureSeverity.HIGH,
        ("PR33", "business_genome_calibration_v0_1"),
        "Reply-stage or human-agreement success is not contract/order/ROI success; outcome stages must remain separate.",
        ("stage_specific_outcomes", "raw_denominators", "no_roi_claim_without_final_outcome"),
    ),
    FailurePattern(
        "F012_MATURITY_INFLATION_FALSE_COMPLETION",
        ("evaluation", "evolution", "capability_adoption_governor", "forge_lifecycle"),
        FailureSeverity.CRITICAL,
        ("NEXUS_Orchestrator_Audit_Evidence_Pack_v0.1", "PR28"),
        "Designed, implemented, tested and production are distinct states; CI success never proves production or business effectiveness.",
        ("maturity_gate", "production_artifact_verification", "business_outcome_evidence"),
    ),
    FailurePattern(
        "F013_DUPLICATE_OUTREACH",
        ("exact_external_approval", "business_genome", "decision_outcome_learning"),
        FailureSeverity.HIGH,
        ("NEXUS_Master_Context_v1.2", "NEXUS_Graphic_Document_Integrity_Layer_v1.1"),
        "Relationship activity must be deduplicated against the latest thread and prior action state before any new outreach is prepared for release.",
        ("latest_thread_check", "dedupe_key", "relationship_contact_budget"),
    ),
    FailurePattern(
        "F014_CROSS_PROJECT_CONTAMINATION",
        ("evidence_semantics", "requirement_readiness", "cross_project_runtime", "business_genome"),
        FailureSeverity.CRITICAL,
        ("NEXUS_Portfolio_Checkpoint_2026-08-20", "PR7"),
        "Evidence, requirements and decisions must remain project-scoped; similar products or counterparties do not justify cross-project value reuse.",
        ("project_scope_key", "entity_resolution", "source_project_check"),
    ),
    FailurePattern(
        "F015_UNCALIBRATED_SCORE_PRECISION",
        ("evaluation", "business_genome", "capability_adoption_governor"),
        FailureSeverity.HIGH,
        ("NEXUS_Master_Context_v1.1_anti_patterns", "PR28"),
        "Numeric-looking scores must not imply calibrated probability or ROI without sufficient outcome data.",
        ("prefer_ordinal_decision", "preserve_raw_metrics", "calibrate_before_probability"),
    ),
    FailurePattern(
        "F016_LLM_JUDGE_OVERTRUST",
        ("evaluation", "evolution", "public_pattern_reconstruction", "forge_lifecycle"),
        FailureSeverity.HIGH,
        ("REFLECT_2026_arXiv_2605.19196",),
        "LLM judges are advisory for open-ended agent quality; deterministic checks, evidence verification and controlled interventions remain required for promotion-critical evaluation.",
        ("deterministic_first", "judge_meta_evaluation", "human_or_verifiable_tiebreak"),
    ),
    FailurePattern(
        "F017_PROMPT_INJECTION_TOOL_POISONING",
        ("security_policy_threat_model", "capability_action_routing", "cross_project_runtime"),
        FailureSeverity.CRITICAL,
        ("AgentPI_2026_arXiv_2602.10453", "AI_dev_tool_PI_2026_arXiv_2603.21642"),
        "External content, tool descriptions and MCP outputs are untrusted observations and must never become authorization or hidden control-plane instructions.",
        ("separate_data_from_control", "parameter_visibility", "sandbox_and_action_gate", "audit_tool_calls"),
    ),
    FailurePattern(
        "F018_MEMORY_WRITE_WITHOUT_RETRIEVAL",
        ("forge_lifecycle", "decision_outcome_learning", "cross_project_runtime", "evolution"),
        FailureSeverity.HIGH,
        ("AgentMemorySurvey_2026_arXiv_2603.07670", "EvoMemBench_2026_arXiv_2605.18421"),
        "Stored lessons do not improve decisions unless relevant memory is retrieved, contradiction-managed and applied before action.",
        ("write_manage_read_loop", "task_conditioned_retrieval", "contradiction_check", "forget_or_supersede_stale_memory"),
    ),
)

FAILURE_PATTERNS: tuple[FailurePattern, ...] = _PATTERNS
FAILURE_BY_ID: Mapping[str, FailurePattern] = MappingProxyType({p.failure_id: p for p in _PATTERNS})


def validate_failure_memory() -> tuple[str, ...]:
    errors: list[str] = []
    ids: set[str] = set()
    for pattern in FAILURE_PATTERNS:
        if pattern.failure_id in ids:
            errors.append(f"duplicate failure_id:{pattern.failure_id}")
        ids.add(pattern.failure_id)
        if not pattern.failure_id.strip() or pattern.failure_id != pattern.failure_id.strip():
            errors.append("invalid failure_id")
        if not pattern.concerns or len(set(pattern.concerns)) != len(pattern.concerns):
            errors.append(f"invalid concerns:{pattern.failure_id}")
        if not pattern.evidence_refs or len(set(pattern.evidence_refs)) != len(pattern.evidence_refs):
            errors.append(f"invalid evidence_refs:{pattern.failure_id}")
        if not pattern.lesson.strip():
            errors.append(f"missing lesson:{pattern.failure_id}")
        if not pattern.required_checks or len(set(pattern.required_checks)) != len(pattern.required_checks):
            errors.append(f"invalid required_checks:{pattern.failure_id}")
    return tuple(errors)


def relevant_failures(concern: str) -> tuple[FailurePattern, ...]:
    if not isinstance(concern, str) or not concern.strip() or concern != concern.strip():
        return ()
    return tuple(pattern for pattern in FAILURE_PATTERNS if concern in pattern.concerns)


def relevant_failure_refs(concern: str) -> tuple[str, ...]:
    return tuple(pattern.failure_id for pattern in relevant_failures(concern))
