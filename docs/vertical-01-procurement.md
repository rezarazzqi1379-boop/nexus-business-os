# Vertical 01 — Procurement Signal-to-Outcome

## Objective

Prove that NEXUS can convert real commercial evidence into a structured, auditable learning loop without inventing missing facts.

## Required chain

`Entity → Evidence → Relationship → Signal → Opportunity → Outcome`

## Evidence rule

Every Evidence record must explicitly classify its epistemic status as one of:

`fact | claim | estimate | inference | hypothesis | assumption | unknown`

A direct supplier email is evidence that the supplier made a statement; the statement's technical/commercial content remains a **claim** until independently verified. Observable events such as receiving a catalog can be recorded as **fact**. Classification never upgrades confidence by itself.

## First live cases

1. SupplierTR — supplier **claim** that engineering evaluation started
2. GH Petro — supplier **claim** of relevant OCTG / steel-pipe line experience
3. YAXING — **fact** of technical engagement and catalog receipt; final Hydrotester geometry remains unknown

## Acceptance criteria

A case is considered closed-loop valid only when:

- the entity is resolved to a canonical identity;
- evidence points to a retrievable source;
- evidence has an explicit supported epistemic class;
- relationship and signal both reference that evidence;
- opportunity is derived from the signal, not from unsupported inference;
- outcome is recorded as either a micro-outcome or terminal outcome;
- unknowns remain explicit;
- any external consequential action remains human-gated;
- no duplicate canonical object is created.

## Initial measurable targets

- 3 independent real cases completed end-to-end
- 0 unsupported technical specifications introduced
- 0 supplier claims silently promoted to verified facts
- 0 duplicate canonical objects created
- 100% of progress claims linked to retrievable evidence
- next-best-action accepted or corrected by a human reviewer for each live case

## Non-goals for v0.1

- no autonomous email sending;
- no large agent fleet;
- no automatic deletion/archiving of duplicate Notion databases;
- no attempt to replace Supabase as runtime state;
- no broad multi-vertical platform build before this loop is validated.
