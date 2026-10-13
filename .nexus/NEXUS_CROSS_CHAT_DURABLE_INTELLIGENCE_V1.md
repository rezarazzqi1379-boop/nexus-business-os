# NEXUS CROSS-CHAT DURABLE INTELLIGENCE V1
Status: IMPLEMENTED / PENDING CI
Date: 2026-10-07

## Purpose
Provide one governed, durable recovery layer for NEXUS chats without turning chat memory, agents, plugins or adapters into authority.

## Authority model
Source Registry + relevant canonical project master remain authority selectors.
This durable layer stores evidence-bound operational intelligence and portable checkpoints.
It never overrides a canonical engineering/commercial master.

## Record model
Every durable record carries:
record_id; project_id; kind; subject; predicate; object; evidence_state; source_ref; observed_at; optional valid_from/valid_to; supersedes; origin_id.

Evidence states:
VERIFIED / CLUE / HYPOTHESIS / SUPERSEDED.

## Cross-chat recovery
At the beginning of consequential work:
1. recover Source Registry;
2. select canonical project master;
3. recover latest tested checkpoint;
4. recover only records matching project_id;
5. refresh dynamic facts required by the task;
6. resolve contradictions/supersession;
7. continue from last tested safe state.

No chat may infer authority from memory alone.
No project may inherit facts from another project.
A portable capsule contains IDs and measurements, not hidden authority.

## Storage tiers
T0 Canonical: Source Registry + project masters.
T1 Durable intelligence: evidence/event/entity/relationship records.
T2 Tested code/contracts/checkpoints.
T3 Session working set.
T4 Ephemeral hypotheses/search results.

Promotion T4→T1 requires provenance and classification.
Promotion to VERIFIED requires direct evidence.
Dynamic current facts require freshness validation at use time.

## Permanent collection loop
INGEST → NORMALIZE → ENTITY RESOLVE → DEDUPE ORIGIN → CLASSIFY → LINK → TEMPORALIZE → VERIFY → STORE → CHECKPOINT → RECOVER → REFRESH.

## Network data families
Company/legal entity; site/plant; process/equipment; product/spec; procurement/RFQ/tender; award/incumbent; EPC/OEM; person/role; contactability; trade/customs; logistics/payment/compliance; competitor/supplier; relationship path; current trigger.

## Anti-pollution rules
Historical event != current demand.
Directory contact != buyer authority.
Repeated copy != independent corroboration.
Graph path != proven relationship unless every edge has evidence.
Adapter connected != capability available.
Score != evidence.
Memory != authorization.

## Cross-chat acceptance
A new compatible chat must be able to recover project scope, record IDs, evidence states, independent-origin count, latest tested repo/CI checkpoint and next safe action without copying mutable facts into global instructions.
