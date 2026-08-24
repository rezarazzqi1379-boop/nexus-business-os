# NEXUS Meta-Agent v2 — Research and Experiment Record

Date: 2026-08-21

## Status

Experimental candidate. It does not replace the NEXUS v1.9 approval, audit, evidence, project-isolation, or runner controls.

## Research coverage

Eight independent discovery workstreams reviewed 200 search results spanning production agent frameworks, MCP servers, multi-agent orchestration, research agents, coding agents, enterprise connectors, local/desktop agents, and agent-memory/evaluation research. Search results were treated as discovery evidence, not proof of safety or superiority.

High-signal primary-source patterns were taken from OpenAI Agents SDK, Microsoft Agent Framework, LangGraph, Google ADK, AutoGen, Semantic Kernel, CrewAI, PydanticAI, LlamaIndex, Haystack, MCP specifications/registry/reference servers, Playwright MCP, OpenWorker, SWE-agent/OpenHands-style coding agents, and recent agent-memory/evaluation research.

## Synthesis

The useful common denominator is not a persona or a large team of simulated agents. It is a small control plane with:

1. typed evidence and explicit claim classes;
2. project-isolated memory;
3. capability-based tool selection;
4. a declared risk ceiling;
5. deterministic planning where possible;
6. human approval for external consequences;
7. durable outcome records;
8. forward-only recovery;
9. evaluation before promotion;
10. no self-modification of production controls.

## Novel hypothesis

A provider-neutral meta-agent that selects atomic capabilities under a risk ceiling will be easier to test and safer to evolve than a fixed collection of many role-playing agents.

## Baseline

NEXUS Autopilot v1.9: 104 tests, fixed runner registry, approval gate, audit/evidence contracts, project isolation and disabled-by-default MCP candidates.

## Candidate change

`meta_agent.py` adds typed capability selection, project-scoped evidence digests, outcome recording and experiment-only improvement proposals. It deliberately produces plans, not authority.

## Admission criteria

The candidate may move forward only if it keeps all v1.9 regressions green, passes its added tests, remains deterministic on repeated inputs, never self-authorizes an external action, and demonstrates improvement on at least one real NEXUS workflow.

## Known limits

- The research pass reviewed 200 result slots, not 200 independently audited codebases.
- Search-result overlap and framework marketing claims remain possible.
- No live model/API, production connector or Windows OpenWorker binary was used.
- Business-value improvement is unproven until a real workflow A/B evaluation is run.
