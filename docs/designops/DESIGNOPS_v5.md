# NEXUS DesignOps v5

Status: ACTIVE ARCHITECTURE / NO CORPORATE MASTER RELEASED

## Purpose
Prevent visual, numeric, provenance and communication errors in ATF catalogs, letterheads, images and outbound documents.

## Release gates
DRAFT -> CANDIDATE -> APPROVAL_READY -> RELEASED

Only RELEASED artifacts may be used externally. RELEASED requires deterministic QA, visual QA, provenance checks, regression checks and explicit human approval.

## Source-of-truth order
1. Verified NEXUS canonical company registry for legal/contact facts.
2. Approved Visual Source Map for logos, letterheads, stamps, signatures and layout references.
3. Current project evidence for project-specific facts.
4. Design tools are render/edit workspaces, never authoritative fact sources.

## Permanent regressions
- Never synthesize or approximate an official logo, stamp or signature.
- Never infer legal/contact facts.
- Never leak stale date, recipient, attachment or project fields from historical documents.
- Broken/unshaped Persian RTL blocks promotion.
- Rejected stamp assets block promotion.
- Human visual rejection overrides machine PASS and reopens QA.
- Canonical registry wins over conflicting design content.

## Connector roles
- Canva: downstream editable workspace; not brand truth until an approved ATF Brand Kit exists.
- Figma: inspection/reference until write permission is available.
- GitHub: versioned code, tests, rules, audit trail and CI.

## Learning rule
A failure may propose a new rule and regression test, but must not silently self-activate into production policy without validation.
