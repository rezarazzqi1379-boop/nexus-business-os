# AI Resource Router CI Gate v0.1

Status: IMPLEMENTED / CI PROOF PENDING

This change records the integration gate for the governed AI Resource Router introduced in PR #56.

Acceptance requirements:

1. canonical repository CI must run on the exact PR head;
2. compile and existing canonical regression tests must pass;
3. router tests must pass without network access or credentials;
4. FreeLLM remains discovery-only and cannot self-promote claims;
5. confidential/restricted inputs remain fail-closed unless a provider is explicitly approved;
6. no provider call, spend, credential use, deployment, email send, or other external effect is introduced by this PR;
7. merge does not imply production readiness.

Promotion beyond merged-shadow status requires separate live provider verification, privacy review, eval/latency/cost evidence, secrets handling, rollback documentation, and explicit production authorization.
