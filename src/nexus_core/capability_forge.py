from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Domain = Literal[
    "EXECUTIVE", "COMMERCIAL", "ENGINEERING", "RESEARCH", "CODING", "MEMORY",
    "AUTOMATION", "SECURITY", "DESIGN", "DEPLOYMENT", "DATA", "COMMUNICATION"
]
CapabilityState = Literal[
    "WORKING", "PARTIAL", "GAP", "EXPERIMENT", "DEFERRED", "BLOCKED", "SUPERSEDED"
]
Action = Literal["KEEP", "BUILD", "BENCHMARK", "CONNECT", "DEFER", "REPAIR", "RETIRE"]

_ALLOWED_DOMAINS = {
    "EXECUTIVE", "COMMERCIAL", "ENGINEERING", "RESEARCH", "CODING", "MEMORY",
    "AUTOMATION", "SECURITY", "DESIGN", "DEPLOYMENT", "DATA", "COMMUNICATION"
}
_ALLOWED_STATES = {"WORKING", "PARTIAL", "GAP", "EXPERIMENT", "DEFERRED", "BLOCKED", "SUPERSEDED"}
_ALLOWED_ACTIONS = {"KEEP", "BUILD", "BENCHMARK", "CONNECT", "DEFER", "REPAIR", "RETIRE"}


@dataclass(frozen=True)
class CapabilityRecord:
    capability_id: str
    name: str
    domain: Domain
    state: CapabilityState
    action: Action
    problem: str
    current_mechanism: str
    candidate_refs: tuple[str, ...]
    project_refs: tuple[str, ...]
    acceptance_test: str
    rollback: str
    frequency: int
    impact: int
    safety_risk: int
    overlap_risk: int
    evidence_refs: tuple[str, ...] = ()
    revisit_triggers: tuple[str, ...] = ()

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field_name in (
            "capability_id", "name", "problem", "current_mechanism", "acceptance_test", "rollback"
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} is required")
        if self.domain not in _ALLOWED_DOMAINS:
            errors.append("unsupported domain")
        if self.state not in _ALLOWED_STATES:
            errors.append("unsupported state")
        if self.action not in _ALLOWED_ACTIONS:
            errors.append("unsupported action")
        for field_name in ("frequency", "impact", "safety_risk", "overlap_risk"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or not 0 <= value <= 5:
                errors.append(f"{field_name} must be integer 0..5")
        if len(set(self.candidate_refs)) != len(self.candidate_refs):
            errors.append("duplicate candidate_refs")
        if len(set(self.project_refs)) != len(self.project_refs):
            errors.append("duplicate project_refs")
        if self.action == "CONNECT" and not self.candidate_refs:
            errors.append("CONNECT requires at least one candidate_ref")
        if self.action in {"BUILD", "BENCHMARK", "CONNECT", "REPAIR"} and not self.acceptance_test.strip():
            errors.append("active improvement requires acceptance_test")
        return tuple(errors)


def validate_capabilities(records: Sequence[CapabilityRecord]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    for item in records:
        errors.extend(f"{item.capability_id}: {error}" for error in item.validate())
        if item.capability_id in seen:
            errors.append(f"duplicate capability_id: {item.capability_id}")
        seen.add(item.capability_id)
    return tuple(errors)


def priority_score(item: CapabilityRecord) -> int:
    """Deterministic prioritization signal, not probability or authority.

    Rewards repeated/high-impact gaps and penalizes safety exposure and duplicate architecture.
    """
    errors = item.validate()
    if errors:
        raise ValueError("invalid capability: " + "; ".join(errors))
    state_bonus = {
        "GAP": 5,
        "BLOCKED": 4,
        "PARTIAL": 3,
        "EXPERIMENT": 2,
        "WORKING": 0,
        "DEFERRED": -2,
        "SUPERSEDED": -5,
    }[item.state]
    return 3 * item.impact + 2 * item.frequency + state_bonus - 2 * item.safety_risk - item.overlap_risk


def ranked_improvements(records: Sequence[CapabilityRecord]) -> tuple[CapabilityRecord, ...]:
    errors = validate_capabilities(records)
    if errors:
        raise ValueError("invalid capability portfolio: " + "; ".join(errors))
    actionable = [r for r in records if r.action in {"BUILD", "BENCHMARK", "CONNECT", "REPAIR"}]
    return tuple(sorted(actionable, key=lambda r: (-priority_score(r), r.capability_id)))


def candidates_for_domain(records: Sequence[CapabilityRecord], domain: Domain) -> tuple[CapabilityRecord, ...]:
    if domain not in _ALLOWED_DOMAINS:
        raise ValueError("unsupported domain")
    return tuple(r for r in records if r.domain == domain and r.state != "SUPERSEDED")


def should_revisit(item: CapabilityRecord, trigger: str) -> bool:
    return item.state == "DEFERRED" and trigger in item.revisit_triggers


def capability_portfolio() -> tuple[CapabilityRecord, ...]:
    """Cross-domain NEXUS capability map.

    The map is intentionally broader than the runtime. Candidate refs point to the persistent
    agent/tool catalog, but no capability record grants installation, external access, merge,
    deployment or production authority.
    """
    return (
        CapabilityRecord(
            "CAP-EXEC-PORTFOLIO", "Governed portfolio control", "EXECUTIVE", "WORKING", "KEEP",
            "Recover project state, preserve authority and choose safe next work across programs.",
            "Portfolio Control Plane + Canonical Authority + Executive Kernel",
            (), ("PRJ-HYD-01", "PRJ-HTL-01", "PRJ-KCL-01", "PRJ-CAN-01"),
            "Every portfolio projection preserves project state locks and blocks consequential auto-actions.",
            "Revert to prior canonical main commit.", 5, 5, 2, 1,
            ("master:NEXUS_Master_Context:v1.9", "registry:NEXUS_Source_Registry:v1.6"),
        ),
        CapabilityRecord(
            "CAP-CODE-SANDBOX", "Measured coding sandbox", "CODING", "GAP", "BENCHMARK",
            "Coding workers need isolated reproducible repo execution with measurable comparison and rollback.",
            "GitHub branches/CI + governed worker contracts; no proven live sandbox winner yet.",
            ("AGT-OPENAI-SANDBOX", "AGT-OPENCODE", "AGT-OPENHANDS", "AGT-GOOSE", "AGT-OPEN-SWE"),
            ("NEXUS_CORE",),
            "Run one frozen sanitized coding task through baseline and candidates; require same snapshot, zero policy/security regressions, passing tests and lower correction/time/cost on >=3 clean runs.",
            "Discard sandbox/experiment branch and retain current GitHub+CI execution path.", 5, 5, 3, 2,
            revisit_triggers=("coding-arena-ready",),
        ),
        CapabilityRecord(
            "CAP-MEMORY-LONGTERM", "Versioned experiential memory", "MEMORY", "PARTIAL", "BENCHMARK",
            "Project context is versioned, but reusable agent experience/skill learning across long horizons remains incomplete.",
            "Canonical masters + Source Registry + project/chat indexes + GitHub artifacts.",
            ("AGT-OPENAI-AGENTS-SDK", "AGT-LANGGRAPH"), ("NEXUS_CORE",),
            "Compare current retrieval/context path with one versioned memory adapter on repeated tasks; no cross-project leakage, stale-authority promotion or untraceable memory rewrite.",
            "Disable memory adapter; keep canonical files/registry as authority.", 4, 5, 4, 3,
            revisit_triggers=("repeated-context-loss", "memory-benchmark-ready"),
        ),
        CapabilityRecord(
            "CAP-RESEARCH-SCOUT", "Persistent research and technology scout", "RESEARCH", "WORKING", "KEEP",
            "Continuously discover tools/agents/MCPs without forgetting deferred candidates.",
            "Technology Radar + Agent Catalog + weekly Agent Catalog Scout.",
            ("AGT-MCP-OFFICIAL-REGISTRY",), ("NEXUS_CORE",),
            "Weekly scout produces deduplicated, source-backed lifecycle deltas and never auto-installs/promotes candidates.",
            "Disable scout automation; retain persistent catalog snapshot.", 4, 4, 2, 1,
        ),
        CapabilityRecord(
            "CAP-MCP-DISCOVERY", "Governed MCP discovery", "AUTOMATION", "EXPERIMENT", "BUILD",
            "Need broad tool discovery while preventing unverified MCP servers from becoming executable authority.",
            "MCP Broker policy exists; official registry ingestion is not yet wired into a live sandbox feed.",
            ("AGT-MCP-OFFICIAL-REGISTRY",), ("NEXUS_CORE",),
            "Ingest registry metadata read-only, dedupe stable server IDs, verify publisher/schema/permissions, and expose zero tools unless deterministic broker checks pass.",
            "Disable registry ingestion and retain static connector/tool registry.", 3, 4, 4, 1,
            revisit_triggers=("mcp-scout-ready",),
        ),
        CapabilityRecord(
            "CAP-DURABLE-WAIT", "Crash-safe multi-day execution", "AUTOMATION", "DEFERRED", "DEFER",
            "Supplier/RFQ workflows may eventually need reliable resume across days without duplicate side effects.",
            "Current scheduler, automation tasks, queue/idempotency primitives and explicit approval gates.",
            ("AGT-TEMPORAL", "AGT-LANGGRAPH"), ("NEXUS_CORE", "PRJ-HYD-01", "PRJ-KCL-01"),
            "Demonstrate crash/restart during a waiting workflow and resume with zero duplicate external action.",
            "Remove durable-workflow adapter and retain existing scheduler/state.", 2, 4, 3, 3,
            revisit_triggers=("repeated-state-loss", "multi-day-workflow-volume"),
        ),
        CapabilityRecord(
            "CAP-COMMERCIAL-RADAR", "Customer/supplier/opportunity radar", "COMMERCIAL", "PARTIAL", "BUILD",
            "Commercial discovery exists but needs a single measured funnel from signal to qualified opportunity without outreach noise.",
            "Customer Network + Need Radar + live Gmail/CRM research + project-specific source gates.",
            (), ("PRJ-HYD-01", "PRJ-KCL-01", "PRJ-CAN-01"),
            "On a frozen research set, dedupe entities, preserve supplier-vs-buyer roles, attach retrievable evidence, rank opportunities and authorize zero outreach automatically.",
            "Disable new radar projection and retain current customer/need modules.", 5, 5, 4, 2,
        ),
        CapabilityRecord(
            "CAP-ENGINEERING-REVIEW", "Engineering evidence reviewer", "ENGINEERING", "PARTIAL", "BUILD",
            "Supplier proposals need repeatable line-by-line delta review against buyer-controlled engineering masters.",
            "Canonical project masters + project-specific review packets + manual engineering reconciliation.",
            (), ("PRJ-HYD-01", "PRJ-HTL-01", "PRJ-CAN-01"),
            "Given buyer master + supplier proposal, emit requirement-level FACT/CLAIM/UNKNOWN deltas with zero cross-project value transfer and no silent supplier promotion.",
            "Use existing manual/internal comparison packet workflow.", 4, 5, 3, 1,
        ),
        CapabilityRecord(
            "CAP-SECURITY-INGRESS", "Untrusted external ingress and exact action gates", "SECURITY", "PARTIAL", "REPAIR",
            "Email/web/doc content must never alter control-plane authority or reuse approvals after payload changes.",
            "Historical/stacked security PRs contain ingress guard and exact external-action gate behavior; canonical main still needs convergence proof.",
            (), ("NEXUS_CORE",),
            "Adversarial external content cannot set approval/action fields; any material payload/recipient/attachment/source-version change invalidates approval.",
            "Disable converged adapter and retain existing conservative manual approval policy.", 5, 5, 5, 1,
        ),
        CapabilityRecord(
            "CAP-DESIGN-ASSET", "Governed design generation", "DESIGN", "PARTIAL", "DEFER",
            "Design creation exists, but approved asset hashes/roles are not yet canonical authority.",
            "Canva/Figma/design infrastructure + tested token/a11y package; ATF Asset Registry remains pending lock.",
            (), ("NEXUS_CORE",),
            "Approved asset registry binds source files/hashes/roles and publish/share remains explicitly gated.",
            "Keep design outputs as drafts and do not promote asset authority.", 2, 3, 2, 2,
            revisit_triggers=("asset-registry-approved",),
        ),
        CapabilityRecord(
            "CAP-DEPLOYMENT-PROOF", "Deployment and production proof", "DEPLOYMENT", "BLOCKED", "REPAIR",
            "Green CI and deployment existence do not prove healthy production; prior Railway login loop remains unresolved.",
            "GitHub CI + Railway/Vercel/Supabase paths, with production mutations gated.",
            (), ("NEXUS_CORE",),
            "Prove health, authentication, persistence and rollback in staging/shadow before any production promotion.",
            "Rollback deployment/ref to last verified release; preserve current production access controls.", 3, 5, 5, 1,
        ),
        CapabilityRecord(
            "CAP-COMMS-THREAD", "Thread-aware communication preparation", "COMMUNICATION", "WORKING", "KEEP",
            "Prepare outbound communications without duplicate outreach, stale-thread use or project contamination.",
            "Gmail live-thread retrieval + exact approval policy + project evidence packets.",
            (), ("PRJ-HYD-01", "PRJ-KCL-01", "PRJ-CAN-01"),
            "Draft generation always reads latest thread, checks duplicate outreach, binds evidence/source version and leaves send authorization false.",
            "Return to manual drafting with the same latest-thread/evidence checks.", 5, 5, 4, 1,
        ),
    )
