# NEXUS External Tool Bootstrap

Status: IMPLEMENTED + TESTED on feature branch. Not merged. Not deployed.

## Purpose

Coordinate many external tools without confusing registration, connection, read verification, write enablement, or production approval.

## Active stack priority

1. Credential boundary: Bitwarden/Vaultwarden.
2. Observability: PostHog.
3. Orchestration: n8n, never authority.
4. Commercial inbox: Chatwoot.
5. Evidence storage: Nextcloud candidate.
6. Scheduling: Cal.diy candidate.
7. Utility adapters: LibreTranslate, Penpot, Excalidraw, OBS.
8. Existing connected business surfaces: Notion, HubSpot, Canva.

Comparison-only tools are not activated just because they appear in the reviewed reel set.

## Bootstrap behavior

`AccountBootstrapPlanner` prepares all selected providers in parallel and classifies every provider as READY, HANDOFF_REQUIRED, BLOCKED, or SKIPPED.

READY means only that NEXUS can continue machine-side preparation. It does not mean an account exists or the provider is connected.

HANDOFF_REQUIRED means the provider enforces a user-controlled OAuth, CAPTCHA, identity, or similar gate. NEXUS resumes after that gate; it does not bypass it.

BLOCKED is reserved for policy or provider constraints such as payment/material commitments.

SKIPPED means the provider is comparison-only or lacks a measured role in the active stack.

## Current live evidence, 2 Sep 2026

- Notion: READ_VERIFIED.
- HubSpot: READ_VERIFIED; sales-pipeline onboarding goal set successfully. Remaining provider onboarding tasks do not equal NEXUS write authorization.
- PostHog: READ_VERIFIED; governed observability dashboard exists.
- Canva: READ_VERIFIED.
- Supabase: account/project list READ_VERIFIED, discovered project INACTIVE; do not route runtime traffic to it.
- Apollo.io: BLOCKED by invalid access credentials.
- Granola: BLOCKED because connector reports no account created.
- No direct ChatGPT plugins were discovered for n8n, Bitwarden/Vaultwarden, Chatwoot, Nextcloud, Cal.diy, Penpot, LibreTranslate, Excalidraw, or Baserow in the latest plugin search.

## Auth-loop diagnostic correction

A production login symptom reported as repeated username/password prompts has a concrete code-level candidate cause: unauthenticated API responses advertised `WWW-Authenticate: Basic`, which can trigger the browser's native Basic-auth dialog even though the application already has its own cookie-backed login form. The feature branch now keeps proactive Basic/Bearer authentication support but disables the HTTP Basic challenge by default. It can be explicitly re-enabled with `NEXUS_BASIC_CHALLENGE=1` for legacy clients. The login UI was also simplified to request only the access token actually validated by the backend. Regression tests cover the default-off and explicit-opt-in challenge behavior.

This is an IMPLEMENTED + CI-TESTED correction candidate, not production proof. The actual Railway login loop remains unclosed until the exact build is deployed to a controlled target and three clean-session E2E logins pass.

## Fresh provisioning notes

Nextcloud current stable administration documentation supports machine user creation via `occ user:add`, including `--password-from-env`, and app-token creation with `user:auth-tokens:add`. Its Provisioning API can also create and manage users remotely. These facts make Nextcloud a strong candidate for non-interactive bootstrap once a deployment target exists.

Vaultwarden supports disabling public signups while retaining invitation-based provisioning. Production use still requires HTTPS/reverse-proxy hardening, pinned images, backups, and a tested first-user/bootstrap path.

Cal.com API v1 is shut down; any hosted Cal integration must use API v2. Cal.diy/self-host must be treated separately from hosted commercial Cal.com.

## Acceptance rule

A provider is promoted only after live evidence for the next maturity state. No account, credential, deployment, or production capability may be inferred from a plan or manifest.
