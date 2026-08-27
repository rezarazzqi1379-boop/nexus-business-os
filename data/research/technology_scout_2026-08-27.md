# NEXUS Technology Scout — 2026-08-27

Status: research / sandbox planning only. No dependency installation, external connection, credential use, merge, deploy or production mutation is authorized by this file.

## Primary-source candidates refreshed

### 1. OpenAI Agents SDK Sandbox Agents — EXPERIMENT
Primary docs: https://openai.github.io/openai-agents-python/sandbox_agents/

Why it matters: isolated filesystem workspace, shell/file operations, snapshots and resumable sandbox state can reduce custom execution-harness code for bounded coding/document tasks.

Current caution: Sandbox Agents are Beta. API/defaults/capabilities may change before GA.

NEXUS acceptance test: stage one sanitized repository task in a sandbox with network disabled, no production credentials, exact task/snapshot/acceptance contract, then compare against the current NEXUS runner on correctness, regressions, human corrections, duration and cost. Require three clean reproducible runs and a tested rollback before adapter promotion.

### 2. Official MCP Registry + NEXUS MCP Broker — EXPERIMENT
Primary docs: https://registry.modelcontextprotocol.io/docs

Why it matters: turns ad-hoc MCP discovery into a registry-backed candidate feed while NEXUS keeps its own provenance, permission, schema and trust gates.

NEXUS acceptance test: discover candidate servers but expose zero tools to execution until publisher/provenance, transport, permission, secret and side-effect checks pass. Only verified read-only candidates may become sandbox-eligible.

### 3. Temporal — WATCH
Primary docs: https://docs.temporal.io/

Why it matters: durable execution can resume workflows after crashes or outages, including long waits between supplier/customer events.

Why not adopt now: infrastructure and operational complexity are high relative to current proven need. NEXUS already has queue/scheduler/idempotency primitives. Temporal should be benchmarked only when one real multi-day workflow demonstrates a repeated recovery gap.

Acceptance test: crash/restart one waiting workflow, resume from the exact durable state, and prove no duplicate consequential action can occur.

### 4. A2A Protocol — WATCH
Primary docs: https://a2a-protocol.org/v1.0.0/

Why it matters: open interoperability between remote/local agents built with different frameworks can later let NEXUS use specialist agents without making one framework canonical.

Why not adopt now: no current vertical requires remote agent-to-agent federation. Preserve protocol awareness and revisit after the local governed worker path is proven.

### 5. Microsoft Agent Framework — WATCH/BENCHMARK
Primary docs: https://learn.microsoft.com/en-us/agent-framework/

Why it matters: workflow orchestration, persistence/checkpoints and HITL are relevant to NEXUS.

Why not adopt now: substantial overlap with the existing NEXUS control plane. Benchmark only on the same frozen vertical and adopt nothing unless it materially reduces defects or implementation/recovery complexity.

### 6. n8n — ADAPTER EXPERIMENT ONLY
Primary docs: https://n8n.io/ai-agents/

Best role: trigger/schedule/webhook/integration plumbing into NEXUS, not authority or canonical decision state.

Acceptance test: one deduplicated read-only trigger into a NEXUS work item, retry-safe, with external action still blocked by NEXUS approval policy.

## Promotion rule

No candidate is promoted because it is popular, new, open source, vendor-endorsed or benchmark-leading. Promotion requires:

1. a measurable repeated problem;
2. a frozen acceptance contract;
3. sanitized/sandbox execution;
4. zero policy/security/cross-project regressions;
5. at least three reproducible clean runs;
6. measurable benefit over the current baseline;
7. tested rollback;
8. adapter-only integration unless a separately governed architecture decision changes authority.

The implementation gate for this rule is `src/nexus_core/adoption_gate.py`.
