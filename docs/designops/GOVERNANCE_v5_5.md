# NEXUS DesignOps Governance v5.5

## Outgoing numbering
New externally issued documents use unique outgoing numbers per recipient/document instance:

`ATF-{PROJECT_CODE}-{YYYYMMDD}-{SEQ}`

Example: `ATF-KCL-UZ-20260823-001`

Campaign references may exist separately but do not replace outgoing numbers. Revisions of the same issued document retain the outgoing number and add revision/version metadata. Legacy shared references remain historical only.

## Brand family policy
No current ATF visual family is silently promoted to corporate master. Mixing components from different visual families in one document is a hard block. A master requires verified logo, typography, grid, footer/contact rules, RTL counterpart, QA examples, and human approval.

## Address policy
Address variants are normalized before contradiction detection. Compact and full versions may both be valid if components are compatible. Conflicting city/province/unit is a block. Missing components are not inferred from unrelated documents.

## Artifact fingerprint policy
File identity is based on SHA-256 content hash, not filename alone.

- Same filename + different hash = different version.
- Different filename + same hash = duplicate copy.
- Only APPROVED/RELEASED hashes may serve as production baselines.

## Release status
Corporate signed/stamped master remains blocked until official logo, verified seal artwork, approved signature, and English/Persian masters are verified and approved.
