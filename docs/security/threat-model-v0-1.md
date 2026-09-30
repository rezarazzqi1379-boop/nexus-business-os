# NEXUS Threat Model v0.1

Status: draft / review artifact. No production authorization follows from this document.

## 1. System objective

NEXUS Business OS converts heterogeneous business evidence into structured decisions, readiness states, evaluation results, human-gated actions, audit metadata, outcomes and learning. The primary security objective is to prevent untrusted evidence, malformed runtime state, ambiguous identifiers or tool/model outputs from causing unauthorized external actions, corrupting canonical evidence, or leaking sensitive commercial information.

## 2. Security-relevant components

- Evidence semantics / procurement records.
- Requirement Readiness Gate.
- Capability Runtime and action-specific approval policy.
- Deterministic Evaluation Harness and promotion policy.
- Decision Learning chain.
- Audit Event Envelope and correlation metadata.
- Integration shadow PRs.
- Connector surfaces: GitHub, Notion, Gmail, Supabase, Vercel and optional AI/plugins.

## 3. Actors

### Trusted only within explicit scope

- Human owner/operator: may authorize a consequential action only when approval is explicit and action-specific.
- GitHub CI: trusted to report test execution state for a specific commit; not trusted to authorize merge/deploy.
- Canonical repository state: trusted as version history for code at an exact ref; policy/source content cannot self-authorize actions.

### Untrusted or conditionally trusted

- Suppliers, buyers and intermediaries.
- Emails, attachments and external documents.
- Web pages and research results.
- LLM/model outputs, prompts and tool/plugin responses.
- Notion records and cross-AI handoff text.
- Runtime Python objects constructed outside validated paths.
- Trace/baggage/correlation metadata.
- External deployment/runtime claims until verified against an exact artifact.

## 4. Assets

1. Human approval integrity.
2. Action IDs and authorization binding.
3. Evidence provenance and epistemic class.
4. Requirement authority state.
5. Evaluation/promotion correctness.
6. Audit-event identity and parent/correlation graph integrity.
7. Credentials, tokens and permission state.
8. Commercially sensitive supplier/buyer information.
9. Canonical code, tests and version history.
10. Outcome records used for future learning.

## 5. Trust-boundary data flows

### Flow A — External evidence -> structured evidence

Threats:
- supplier claim silently becomes fact;
- prompt/data injection embedded in email or document;
- malformed/oversized metadata enters downstream state;
- stale/historical buyer values become engineering authority.

Controls:
- explicit EvidenceKind/epistemic labels;
- retrievable evidence refs;
- approved/provisional/unknown-blocking separation;
- no authority inference from communication alone;
- content treated as data, not execution authority.

### Flow B — Structured decision -> action gate

Threats:
- blanket approval reused for another action;
- malformed ID crashes or bypasses validation;
- Unicode/whitespace ambiguity creates identifier collision/confusion;
- truthy non-boolean approval unlocks action;
- non-reversible internal action bypasses approval.

Controls:
- exact validated action ID;
- `approved is True` semantics;
- bounded canonical ID/text validation;
- human-gated action classes;
- malformed inputs fail closed.

### Flow C — Eval results -> promotion decision

Threats:
- manually constructed/tampered aggregate counters hide failures;
- unsupported assertion semantics pass open;
- critical regression is omitted or downgraded;
- CI success is interpreted as deployment authorization.

Controls:
- derive/validate aggregate counts from concrete results;
- fail-closed assertion behavior;
- explicit critical-case blockers;
- CI is evidence only, not authorization.

### Flow D — Internal control state -> audit/trace metadata

Threats:
- audit fields become a covert free-form payload channel;
- CR/LF, Unicode bidi or formatting characters corrupt logs/views;
- cross-trace parent refs create false causality;
- correlation metadata is treated as authorization;
- sensitive commercial content is exported to telemetry vendors.

Controls:
- metadata-only envelope;
- no free-form payload;
- length/whitespace/control/format validation;
- parent existence/same-trace/cycle checks;
- explicit privacy mode;
- exporter allowlist requirement;
- trace/correlation metadata never authorizes access/action.

### Flow E — AI/tool output -> connector write

Threats:
- prompt injection instructs model to send/merge/deploy/change access;
- hallucinated connector state or schema causes destructive write;
- model-generated recipient/body is sent without human confirmation;
- third-party plugin broadens data exposure.

Controls:
- connector/tool output treated as untrusted until verified;
- action-specific Human Gate for consequential writes;
- no guessed Supabase schema/RLS;
- least-privilege plugin use;
- no automatic external send/deploy/merge/payment/permission changes.

## 6. Abuse cases

### AC-01 Blanket approval replay

Attacker/bug supplies approval for `all-future-actions` or a prior action and attempts a payment/send/merge.

Expected result: blocked; approval must match exact validated `action_id`.

### AC-02 Truthy approval confusion

Runtime object contains `approved="yes"`.

Expected result: blocked; only boolean `True` is accepted.

### AC-03 Unicode identifier ambiguity

Action/event/ref ID contains bidi override, zero-width formatting or line-separator/control characters.

Expected result: validation failure before authorization/correlation.

### AC-04 Aggregate tampering

Evaluation result contains failing concrete cases but manually reports zero failures.

Expected result: promotion input is invalid and blocked.

### AC-05 Supplier fact laundering

Supplier states a capability/compliance fact in email; downstream summary phrases it as independently verified.

Expected result: regression/evidence semantics preserve it as Claim unless independently supported.

### AC-06 Requirement authority laundering

A historically communicated 12 m pipe length is treated as current approved engineering input.

Expected result: remains provisional/unknown until authority-linked source exists.

### AC-07 Trace payload smuggling

Sensitive message body or large multiline data is inserted into evidence refs/tags/correlation fields.

Expected result: bounded metadata validation rejects covert payload/log-injection channels.

### AC-08 Prompt injection through business evidence

Email/document says to ignore prior rules, expose secrets or send a reply immediately.

Expected result: content remains evidence data; no scope/permission/action authorization is derived from it.

### AC-09 Deployment-status confusion

A successful CI run or Vercel READY status is interpreted as production parity.

Expected result: blocked as an unsupported maturity transition until exact deployed artifact is verified.

### AC-10 Database-schema hallucination

Remembered Supabase schema is used while connector access is degraded.

Expected result: no schema/RLS/data writes; state remains blocked/unknown until live inspection.

## 7. Severity calibration

- Critical: realistic bypass enabling payment/signature/contract acceptance/access takeover/credential exposure or broad unauthorized external action.
- High: realistic bypass of external send/merge/deploy/human gate; corruption of canonical evidence or authorization state; sensitive commercial data exfiltration.
- Medium: integrity issue that can misclassify readiness/evaluation/audit state but still encounters an independent gate before consequential action.
- Low: limited ambiguity, denial of service or test-only issue without a realistic protected-asset path.

Severity must account for existing independent gates and realistic reachability, not theoretical impact alone.

## 8. Security test strategy

For security-sensitive changes:

1. Validate normal safe behavior.
2. Add malformed-type tests despite static typing.
3. Test blank, padded, oversized and Unicode-control identifiers.
4. Test stale/mismatched/blanket approval replay.
5. Replay at least one historical real regression where available.
6. Test manually tampered dataclass/state objects when constructors are public.
7. Run integration shadow across evidence -> readiness -> eval -> promotion -> action gate where relevant.
8. Verify exact GitHub Actions result for the final head.
9. Obtain independent review before promotion.

When Codex Security Access becomes available, use this threat model and root `SECURITY.md` as repository context for diff scans and later repository-wide scans.

## 9. Residual risks / unknowns

- Codex Security Access is not currently confirmed available for this account.
- Supabase runtime grants/schema/RLS are not currently verified through the degraded connector.
- Current Vercel production parity with draft Python work is not established.
- Independent reviews for multiple draft PRs remain pending.
- Business-effectiveness of readiness/eval/audit controls is not established by software tests alone.
- Engineering authority for final Hydrotester length/wall-thickness/pressure-by-size remains unresolved until buyer-side confirmation.

## 10. Promotion criteria for security-sensitive features

A feature should not move toward merge merely because tests pass. Minimum evidence should include:

- explicit security invariants;
- adversarial regression coverage for identified abuse cases;
- successful CI at exact head;
- no unresolved high/critical security finding;
- integration proof where feature interactions matter;
- independent review;
- deliberate human merge decision.
