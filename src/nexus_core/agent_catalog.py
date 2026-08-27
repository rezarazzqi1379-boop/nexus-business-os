from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Kind = Literal[
    "AGENT", "FRAMEWORK", "CODING_AGENT", "BROWSER_AGENT", "MCP_SERVER", "MCP_REGISTRY",
    "PROTOCOL", "MEMORY", "EVAL_OBSERVABILITY", "AUTOMATION", "SANDBOX", "DURABLE_EXECUTION",
    "MODEL_ROUTER", "RESEARCH_AGENT", "VOICE_AGENT", "COMPUTER_USE", "OTHER"
]
Lifecycle = Literal[
    "DISCOVERED", "WATCH", "RESEARCHED", "SANDBOX_READY", "EXPERIMENT", "PILOT",
    "ADOPTED_ADAPTER", "DEFERRED", "SUPERSEDED", "REJECTED", "ARCHIVED"
]

_ALLOWED_KINDS = {
    "AGENT", "FRAMEWORK", "CODING_AGENT", "BROWSER_AGENT", "MCP_SERVER", "MCP_REGISTRY",
    "PROTOCOL", "MEMORY", "EVAL_OBSERVABILITY", "AUTOMATION", "SANDBOX", "DURABLE_EXECUTION",
    "MODEL_ROUTER", "RESEARCH_AGENT", "VOICE_AGENT", "COMPUTER_USE", "OTHER"
}
_ALLOWED_LIFECYCLES = {
    "DISCOVERED", "WATCH", "RESEARCHED", "SANDBOX_READY", "EXPERIMENT", "PILOT",
    "ADOPTED_ADAPTER", "DEFERRED", "SUPERSEDED", "REJECTED", "ARCHIVED"
}


@dataclass(frozen=True)
class AgentCatalogEntry:
    catalog_id: str
    name: str
    kind: Kind
    source_url: str
    observed_at: str
    lifecycle: Lifecycle
    problem_tags: tuple[str, ...]
    capabilities: tuple[str, ...]
    revisit_triggers: tuple[str, ...]
    acceptance_test: str
    rollback: str
    notes: str = ""
    superseded_by: str | None = None

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        for field_name in ("catalog_id", "name", "source_url", "observed_at", "acceptance_test", "rollback"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{field_name} is required")
        if self.kind not in _ALLOWED_KINDS:
            errors.append("unsupported kind")
        if self.lifecycle not in _ALLOWED_LIFECYCLES:
            errors.append("unsupported lifecycle")
        if len(set(self.problem_tags)) != len(self.problem_tags):
            errors.append("duplicate problem_tags")
        if len(set(self.capabilities)) != len(self.capabilities):
            errors.append("duplicate capabilities")
        if self.lifecycle == "SUPERSEDED" and not self.superseded_by:
            errors.append("superseded entry requires superseded_by")
        if self.lifecycle != "SUPERSEDED" and self.superseded_by:
            errors.append("superseded_by only allowed for SUPERSEDED lifecycle")
        return tuple(errors)


def validate_catalog(entries: Sequence[AgentCatalogEntry]) -> tuple[str, ...]:
    errors: list[str] = []
    seen: set[str] = set()
    names: set[tuple[str, str]] = set()
    for item in entries:
        errors.extend(f"{item.catalog_id}: {e}" for e in item.validate())
        if item.catalog_id in seen:
            errors.append(f"duplicate catalog_id: {item.catalog_id}")
        seen.add(item.catalog_id)
        key = (item.kind, item.name.casefold())
        if key in names:
            errors.append(f"duplicate kind/name: {item.kind}/{item.name}")
        names.add(key)
    ids = {e.catalog_id for e in entries}
    for item in entries:
        if item.superseded_by and item.superseded_by not in ids:
            errors.append(f"{item.catalog_id}: superseded_by target missing")
    return tuple(errors)


def active_catalog(entries: Sequence[AgentCatalogEntry]) -> tuple[AgentCatalogEntry, ...]:
    errors = validate_catalog(entries)
    if errors:
        raise ValueError("invalid catalog: " + "; ".join(errors))
    return tuple(e for e in entries if e.lifecycle not in {"REJECTED", "ARCHIVED", "SUPERSEDED"})


def candidates_for_problem(entries: Sequence[AgentCatalogEntry], problem_tag: str) -> tuple[AgentCatalogEntry, ...]:
    active = active_catalog(entries)
    return tuple(sorted((e for e in active if problem_tag in e.problem_tags), key=lambda e: (e.lifecycle, e.catalog_id)))


def should_revisit(entry: AgentCatalogEntry, trigger: str) -> bool:
    if entry.lifecycle in {"REJECTED", "ARCHIVED"}:
        return False
    return trigger in entry.revisit_triggers


def seed_catalog() -> tuple[AgentCatalogEntry, ...]:
    """Persistent starter catalog. Discovery breadth is intentionally wider than current adoption.

    Entries are retained even when deferred. Sources are discovery/provenance anchors, not authority.
    """
    return (
        AgentCatalogEntry("AGT-OPENAI-AGENTS-SDK", "OpenAI Agents SDK", "FRAMEWORK", "https://openai.github.io/openai-agents-python/", "2026-08-27", "EXPERIMENT", ("agent-runtime", "tool-orchestration", "hitl"), ("agents", "handoffs", "guardrails", "sessions", "tracing", "mcp"), ("need-runtime-benchmark", "sdk-major-change"), "Run one governed read-only NEXUS vertical with zero authority regressions and full trace correlation.", "Remove adapter and route to existing NEXUS runner."),
        AgentCatalogEntry("AGT-OPENAI-SANDBOX", "OpenAI Sandbox Agents", "SANDBOX", "https://openai.github.io/openai-agents-js/guides/sandbox-agents/", "2026-08-27", "EXPERIMENT", ("coding-sandbox", "workspace-state", "resume"), ("isolated-workspace", "shell", "files", "snapshots", "resume"), ("coding-vertical-ready", "beta-graduation"), "Complete one frozen coding task in an isolated workspace, pass tests, preserve rollback and emit no external side effect.", "Discard sandbox snapshot and use current runner."),
        AgentCatalogEntry("AGT-OPENCODE", "OpenCode", "CODING_AGENT", "https://opencode.ai/", "2026-08-27", "EXPERIMENT", ("coding-agent", "multi-model", "repo-work"), ("terminal-agent", "multi-provider", "plan-build-modes"), ("provider-policy-verified", "new-major-release"), "Beat current coding baseline on same snapshot without policy, security or regression failures.", "Disable worker adapter and revert to current coding path."),
        AgentCatalogEntry("AGT-OPENHANDS", "OpenHands", "CODING_AGENT", "https://www.openhands.dev/", "2026-08-27", "WATCH", ("coding-agent", "agent-control-plane", "multi-agent"), ("coding-agents", "worktrees", "automation", "agent-control-plane"), ("coding-plane-benchmark", "acp-stable"), "Benchmark the same frozen repo task; require lower correction burden or materially better parallel execution.", "Discard benchmark branch; no canonical migration."),
        AgentCatalogEntry("AGT-GOOGLE-ADK", "Google Agent Development Kit", "FRAMEWORK", "https://google.github.io/adk-docs/", "2026-08-27", "WATCH", ("agent-runtime", "multi-agent", "evals"), ("agents", "tools", "mcp", "openapi", "evals", "hitl"), ("framework-benchmark-needed",), "Benchmark one NEXUS vertical against current runtime and Agents SDK.", "Discard benchmark adapter."),
        AgentCatalogEntry("AGT-MS-AGENT-FRAMEWORK", "Microsoft Agent Framework", "FRAMEWORK", "https://learn.microsoft.com/en-us/agent-framework/", "2026-08-27", "WATCH", ("workflow-runtime", "checkpointing", "multi-agent"), ("workflows", "hitl", "checkpointing", "mcp", "a2a"), ("durability-gap", "framework-stabilizes"), "Benchmark resumability, correctness and implementation complexity on identical NEXUS workflow.", "Discard benchmark branch."),
        AgentCatalogEntry("AGT-LANGGRAPH", "LangGraph", "FRAMEWORK", "https://docs.langchain.com/oss/python/langgraph/", "2026-08-27", "DEFERRED", ("state-graph", "durable-agent-workflow"), ("stateful-graphs", "checkpointing", "interrupts"), ("existing-state-machine-insufficient",), "Only test if an existing NEXUS workflow cannot be expressed cleanly; require lower defect rate or simpler recovery.", "Retain current NEXUS state machine."),
        AgentCatalogEntry("AGT-TEMPORAL", "Temporal", "DURABLE_EXECUTION", "https://docs.temporal.io/", "2026-08-27", "DEFERRED", ("durable-execution", "multi-day-workflow", "crash-recovery"), ("durable-workflows", "retries", "signals", "timers"), ("repeated-state-loss", "multi-day-workflow-volume"), "Demonstrate crash-safe resume with zero duplicate external actions.", "Remove Temporal worker/service and retain current task state."),
        AgentCatalogEntry("AGT-MCP-OFFICIAL-REGISTRY", "Official MCP Registry", "MCP_REGISTRY", "https://registry.modelcontextprotocol.io/docs", "2026-08-27", "SANDBOX_READY", ("tool-discovery", "mcp-inventory"), ("server-discovery", "versions", "validation", "metadata"), ("mcp-scout-ready", "registry-schema-change"), "Discover servers but expose none until provenance, schema, permissions and side-effect policy pass.", "Disable registry ingestion and keep static catalog."),
        AgentCatalogEntry("AGT-A2A", "A2A Protocol", "PROTOCOL", "https://a2a-protocol.org/", "2026-08-27", "WATCH", ("agent-interoperability", "multi-vendor-agents"), ("agent-to-agent", "discovery", "tasks", "messages"), ("multi-vendor-agent-need", "protocol-stability"), "Connect two sandbox agents through A2A without delegating NEXUS authority or approvals.", "Remove protocol adapter."),
        AgentCatalogEntry("AGT-N8N", "n8n", "AUTOMATION", "https://n8n.io/", "2026-08-27", "WATCH", ("triggers", "integration-plumbing", "scheduling"), ("webhooks", "schedules", "connectors", "workflow-automation"), ("external-trigger-gap", "integration-backlog"), "Trigger one read-only NEXUS workflow with stable IDs, dedupe and blocked external action.", "Disable trigger adapter; canonical logic remains in NEXUS."),
        AgentCatalogEntry("AGT-OPEN-SWE", "Open SWE", "CODING_AGENT", "https://github.com/langchain-ai/open-swe", "2026-08-28", "DISCOVERED", ("coding-agent", "async-engineering"), ("planning", "sandbox", "subagents", "human-feedback", "pull-requests"), ("coding-arena-expansion",), "Run identical frozen coding task in sandbox and compare correction burden, time and regressions.", "Discard experiment branch."),
        AgentCatalogEntry("AGT-GOOSE", "Goose", "CODING_AGENT", "https://github.com/block/goose", "2026-08-28", "DISCOVERED", ("coding-agent", "local-agent"), ("developer-agent", "tool-use", "local-execution"), ("coding-arena-expansion",), "Run identical frozen coding task with no secrets and compare to current baseline.", "Discard experiment branch."),
        AgentCatalogEntry("AGT-PLANDEX", "Plandex", "CODING_AGENT", "https://github.com/plandex-ai/plandex", "2026-08-28", "DISCOVERED", ("coding-agent", "large-codebase"), ("planning", "repo-context", "code-generation"), ("large-repo-context-gap",), "Test on one large-context refactor with frozen acceptance criteria.", "Discard experiment branch."),
        AgentCatalogEntry("AGT-BYTEBOT", "Bytebot", "BROWSER_AGENT", "https://github.com/bytebot-ai/bytebot", "2026-08-28", "DISCOVERED", ("browser-automation", "computer-use"), ("browser-control", "desktop-automation"), ("browser-vertical-needed",), "Complete a read-only browser task in isolated environment with zero unauthorized action.", "Remove browser adapter."),
        AgentCatalogEntry("AGT-UI-TARS", "UI-TARS Desktop", "COMPUTER_USE", "https://github.com/bytedance/UI-TARS-desktop", "2026-08-28", "DISCOVERED", ("computer-use", "gui-automation"), ("desktop-control", "visual-agent"), ("gui-workflow-gap",), "Complete one sandbox GUI task with deterministic stop conditions and no credential exposure.", "Remove desktop adapter."),
    )
