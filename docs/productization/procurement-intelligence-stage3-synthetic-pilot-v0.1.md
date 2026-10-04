# Procurement Intelligence — Stage 3 Synthetic Company Pilot Packet v0.1

Status: INTERNAL SYNTHETIC PILOT ONLY
Decision boundary: no external contact, no real second-company data, no merge/deploy authorization.

## Purpose
Prove that the same Procurement Intelligence contract can onboard and evaluate a second company without tenant-specific code branches, while preserving tenant/project/evidence/case/human-gate isolation.

## Synthetic company
- tenant_id: `beta`
- organization: `Synthetic Beta Co`
- enabled workflows: `hydrotester`, `can_forming`
- required evidence class: `sourced_claim`
- tenant-specific gated action: `export_packet`
- globally consequential actions remain human-gated.

## Pilot inputs
### Case A — Hydrotester
- case_id: `beta::hydrotester-rev1-2`
- requirement_version: `1.2`
- evidence: `beta::buyer-rev1.2`, `beta::supplier-quote-gh`
- evidence classes: `fact`, `sourced_claim`
- expected decision: `modify`
- expected blocker: unresolved pipe-end condition
- expected action mode: internal for analysis; human-gated for any external send/export.

### Case B — Can Forming
- case_id: `beta::can-forming-d73-d99`
- requirement_version: `scope-v1`
- evidence: `beta::buyer-upgrade-scope`, `beta::golden-eagle-material`
- evidence classes: `fact`, `sourced_claim`
- expected decision: `modify`
- expected blocker: full-line quote not yet equivalent to requested upgrade scope
- expected action mode: internal for normalization; human-gated for any external send/export.

## Stage 3 exit criteria
PASS only if all are true:
1. Both synthetic cases validate through the same shared `ProductizationRecord`/validation code used by the first tenant.
2. No tenant-specific code branch or validator is introduced.
3. Case IDs and evidence refs remain tenant-scoped.
4. Unknown/missing tenant, cross-tenant evidence, cross-tenant case, unauthorized project, and config substitution fail closed.
5. Tenant-specific `export_packet` and globally consequential actions cannot run as internal actions.
6. Outputs cannot invent evidence not present in inputs.
7. Stage 1 remains true for the original internal workflows.
8. CI is green on the exact Stage 3 head.

## Negative findings / non-claims
- Synthetic portability is not proof of real customer value.
- CI success is implementation evidence, not business outcome.
- No claim of product-market fit, ROI, margin improvement, conversion improvement, or reduced onboarding cost is allowed from Stage 3 alone.
- Stage 4 requires fresh exact human approval before any real external pilot or real second-company data/contact.

## Stage 4 gate packet (not authorized)
A future real pilot must specify exact company, approved data scope, exact users/recipients, allowed integrations, confidentiality/privacy boundary, human-gated actions, success metrics, rollback/exit criteria, and explicit authorization for any external contact or real customer data use.

## Measurable pilot scoreboard
- shared-core reuse: required = yes
- tenant-specific code branches: required = 0
- isolation failures: required = 0
- invented evidence: required = 0
- unauthorized consequential actions: required = 0
- regression failures: required = 0
- business outcome: unknown / not measurable in synthetic Stage 3
