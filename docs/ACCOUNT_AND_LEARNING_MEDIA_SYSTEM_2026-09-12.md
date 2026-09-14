# External Account and Learning-Media System

## Inventory result

All repository Python/JavaScript automation, agent primitives, `data/research`, and
`data/operational` records were inspected, excluding the new `data/nexus_system`
runtime. No prior account-onboarding, OAuth callback, credential vault, video
download, transcription, FFmpeg, speech-to-text, OCR, or media-fingerprint runtime
exists. Existing provider records are research candidates and grant no signup or
production authority.

## Implemented account boundary

`external_account_orchestrator.py` can research a service, compare plans, validate
an HTTPS signup origin, prepare non-sensitive public fields, identify missing owner
inputs, and generate an exact `ApprovalRequest` bound to the service, plan digest,
owner and expected cost.

It cannot store passwords or identity/payment secrets. Approval and human presence
are separate requirements. Submit, Terms/DPA consent, OAuth scope grant, MFA,
CAPTCHA, KYC and payment remain owner ceremonies in the provider UI. Account creation
does not grant later account use or production access.

## Implemented learning boundary

`learning_media_pipeline.py` accepts metadata and an authorized transcript. It
validates HTTPS provenance, license state, timezone-aware timestamps, ordered
segments and size limits. Instruction-like transcript content is flagged and cannot
teach a Skill. Clean transcript claims remain unverified and require at least two
additional evidence references before an experiment can be proposed. Promotion is
always disabled.

The current version does not download media or run a codec/transcription engine.
That is intentional until sandboxed media parsing, SSRF/redirect controls, duration
and byte limits, copyright/retention rules, and an evaluated ASR adapter exist.

## Activation state

- Policy taxonomy now gates account creation, Terms, KYC, payment linking and paid plans.
- Repository instructions and the NEXUS Skill route future requests through these modules.
- Continuous research includes weekly account-governance and learning-media radars.
- No external account was created because no service, legal owner, jurisdiction,
  approved fields or exact commit approval was supplied.
