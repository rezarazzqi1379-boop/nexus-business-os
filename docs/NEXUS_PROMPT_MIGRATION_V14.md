# NEXUS Prompt Migration and Replacement Plan v14

Status: PREPARED / NOT ACTIVATED.

## Scope

- Existing `.nexus/prompts/NEXUS_GLOBAL_KERNEL_V1.md` and `NEXUS_PARALLEL_CONTINUATION_V13.md` remain unchanged.
- Candidate `NEXUS_GLOBAL_EXECUTION_KERNEL_V14_CANDIDATE.md` is additive.
- Local `.claude/settings.json` is reported modified and MUST NOT be overwritten remotely.
- ChatGPT custom instructions, other conversations, Codex/Claude configuration and production agents cannot be changed globally by this commit.

## Safe migration

1. Read current prompts and local settings from the actual target environment.
2. Make a source-to-target diff, preserving project-specific rules and permissions.
3. Check contradictions against Source Registry and masters.
4. Test with synthetic scenarios: dirty working tree, cross-project claim, stale buyer, red CI, unapproved paid action, duplicate outreach and non-Persian message.
5. Record baseline and candidate results, version and rollback.
6. Request exact approval for any protected configuration changes.
7. Apply only to one sandbox runner, verify readback and observed behavior.
8. Expand to each supported target separately after acceptance.

## Acceptance

No loss of prior canonical rules; no false claim of global activation; no unsafe local overwrite; no cross-project leakage; no paid call without approval; exact-head CI green; rollback tested.

## Local recovery blockers

The reported Windows branch `research/china-sourcing-v0.1` is dirty with modified Claude settings and many untracked files. A GitHub branch change does not recover or replace those files. Obtain actual local read-only inventory before any local mutation.
