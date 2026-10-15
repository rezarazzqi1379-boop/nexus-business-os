# NEXUS Agent-Systems Research Update — 2026-08-23

Status: research input for NEXUS architecture; not production authority by itself.

## Current external findings

### OpenAI
OpenAI's April 2026 Agents SDK update emphasizes long-horizon agents working in controlled sandboxes with standardized harnesses. Current model guidance also recommends lean prompts and exposing only tools relevant to the task; OpenAI reports that, in one internal coding-agent evaluation setting, leaner configurations improved scores while reducing tokens and cost. These results are directional and must be re-evaluated on NEXUS workloads.

Implication for NEXUS:
- prefer minimal mission-specific tool exposure;
- keep task context narrow;
- use sandbox/review branches for code-changing agents;
- evaluate changes on representative NEXUS tasks rather than trusting generic benchmarks.

Sources:
- https://openai.com/index/the-next-evolution-of-the-agents-sdk/
- https://developers.openai.com/api/docs/guides/latest-model

### Anthropic
Anthropic's production multi-agent research architecture uses an orchestrator-worker pattern: a lead agent plans and delegates bounded parallel research tasks, then synthesizes results. Anthropic explicitly notes coordination, evaluation and reliability challenges in multi-agent systems. Their later engineering material also emphasizes harness design, containment and separating the model's reasoning role from execution infrastructure.

Implication for NEXUS:
- keep a small number of durable coordinators;
- spawn bounded mission workers only when parallel exploration has measurable value;
- give each worker a specific objective, scope and expected output;
- preserve durable plans/checkpoints outside the model context;
- cap blast radius for tool-using agents.

Sources:
- https://www.anthropic.com/engineering/multi-agent-research-system
- https://www.anthropic.com/engineering

### Google / A2A
Google's A2A work is now positioned as an open, vendor-neutral interoperability standard for agent collaboration; the protocol was donated to the Linux Foundation. This supports future cross-framework portability, but protocol adoption is not itself a business outcome.

Implication for NEXUS:
- define internal capability/task contracts so they can later map to A2A or similar protocols;
- avoid hard-coding NEXUS orchestration to a single model vendor;
- do not add A2A runtime complexity until a real cross-agent integration needs it.

Source:
- https://opensource.googleblog.com/2026/04/meet-the-a2family.html

## NEXUS synthesis

The external evidence reinforces the current NEXUS direction rather than a large autonomous swarm:

`Project/Goal -> Audit -> Orchestrator -> bounded workers -> Evidence/Authority -> QA -> Approval -> Execution -> Outcome -> Evaluation -> Innovation Forge`

New operating rules inferred for testing:
1. Context minimization is a first-class optimization target.
2. Tool exposure should be mission-specific and least-privilege.
3. Parallel agents need non-overlapping task contracts and a synthesis owner.
4. Long-running work requires explicit durable checkpoints.
5. Interoperability should be designed as a contract layer, not deployed as infrastructure without demand.
6. Architectural changes remain experiment candidates until NEXUS-specific replay/evals show measurable improvement.
