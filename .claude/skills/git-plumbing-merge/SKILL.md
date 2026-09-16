---
name: git-plumbing-merge
description: Merge or manipulate this repo's git history from a device-bridge/sandboxed shell that cannot unlink files under the mounted project folder. Use whenever a git merge, worktree operation, or lock-file error happens while working on nexus-business-os through a remote/device shell, or whenever `git worktree remove` or any git command fails with "Operation not permitted" or "Unable to create index.lock".
---

# Git Plumbing Merge (sandbox-safe)

## Why this exists

This repo is frequently edited through a device-bridge shell (`device_bash`) whose bind-mounted view of the project folder allows **creating** files but not **unlinking** them (`unlink()` fails with `Operation not permitted`, even for git's own temp/lock files after a successful rename). This breaks two very common git flows:

- `git worktree add` / `git worktree remove` — remove fails outright ("cannot remove a locked working tree").
- A stale `index.lock` left behind by ANY git command blocks every subsequent git command in that repo (`fatal: Unable to create index.lock: File exists`), because git can't unlink its own lock after (or during) an aborted operation.

Discovered and root-caused on 2026-09-14 during the `feat/unified-system-governance-v0.1` → `main` merge. Recorded as Expert Foundry experience record `exp-sandbox-git-lock-eperm-20260914` (`.nexus/runtime/expert_foundry/events.jsonl`) — read that record for the original incident narrative.

## Recovery: stale lock files

1. **Never delete a stale lock in place.** Rename it aside instead — a plain rename (`mv`) works because it doesn't require an unlink, ONLY when source and destination are on the **same filesystem** (i.e. still under the mounted project folder). A cross-filesystem `mv` (e.g. into `$HOME`, outside the mount) silently needs an internal copy+unlink and fails the same way.
2. Move it to a clearly-named debris path *inside* the repo but **outside `.git/refs/heads/`** — anything placed inside `refs/heads/` gets treated as a branch-ref candidate by git's ref scanner and will break `git fetch`/`git branch` with `fatal: bad object refs/heads/<name>`. `.git/stray_debris_from_lock_N` is a safe destination.
3. Re-run the git command in a **fresh shell call** — device_bash gives no cwd/env carryover between calls, so a leftover `GIT_INDEX_FILE`/`GIT_WORK_TREE`/`GIT_DIR` from an earlier command in the same call can silently redirect a later command in that same call to the wrong index. When `git status --short | wc -l` looks wrong (e.g. way fewer lines than expected), suspect leftover env vars before suspecting real repo state — verify with a guaranteed-clean new call.

## Doing real merge/rebase work: skip the working tree entirely

Don't use `git worktree add` or a working-tree `git merge`/`git rebase` for anything nontrivial in this sandbox — both routes end in unremovable locks or unremovable worktree registrations. Instead, do the merge purely on git objects, with a scratch index living **outside** the mounted folder (so it can be created *and* deleted normally):

```bash
export GIT_DIR="$REPO/.git"
export GIT_INDEX_FILE="$HOME/scratch-merge.index"   # OUTSIDE the mount — unlink works here
# GIT_WORK_TREE only if you need an actual checkout to run tests against

# 1. Three-way merge purely on trees (no HEAD, no working tree needed):
git read-tree -m --aggressive <merge-base> <ours> <theirs>

# 2. Inspect conflicts (multi-stage entries), if any:
git ls-files -u

# 3. Resolve each conflicting path manually by choosing/writing the winning blob:
git update-index --cacheinfo <mode>,<blob-sha>,<path>

# 4. Materialize the merged tree and commit it:
git write-tree
git commit-tree <tree-sha> -p <parent1-sha> -p <parent2-sha> -m "merge message"
git update-ref refs/heads/<branch> <new-commit-sha>
```

**Do not build the merged tree by starting from one side's tree and only patching the known-conflict paths** — this silently drops every file that exists on only the other side (a real bug hit during the 2026-09-14 merge: 6 `main`-only files were dropped this way). `git read-tree -m --aggressive <base> <ours> <theirs>` is correct because it does a real three-way merge and preserves one-sided adds/deletes automatically. Sanity-check afterward with `git diff --name-status <ours> <merged-tree>` and `git diff --name-status <theirs> <merged-tree>` — every file that changed on only one side should still be present.

## Triaging "conflicts" before trusting them

Before manually resolving any conflict git reports, check whether it's a **real** content difference or just CRLF/LF noise — this repo has picked up both because it's edited from more than one OS/tool:

```bash
diff <(git show REF:path | tr -d '\r') <(git show REF2:path | tr -d '\r')
```

An empty diff after stripping `\r` means the "conflict" is byte-identical content — resolve it by picking either side (doesn't matter which). On the 2026-09-14 merge this cut a ~6000-line raw diff down to ~250 lines of genuine differences (recorded as `exp-crlf-false-conflict-20260914`).

## Two independently-maintained clones of the same repo

If this repo is being edited by more than one AI tool/session with its own separate clone (e.g. a Claude Code clone and a Codex/ChatGPT clone both pushing to the same GitHub remote), expect **add/add conflicts on files both sides independently rebuilt from the same source material but captured at different points** — there is no fixed rule for "which clone is newer," it alternates per file based on which side actually captured the later user-confirmed data. Diff every such conflict individually (content-hash triage above) rather than blanket-picking one side. Recorded as `exp-two-clone-divergence-20260914`.

## After the merge: verify before trusting it

Run the full test suite against the merged tree before updating the branch ref / before telling the user it's done. A merge that only resolves conflicts syntactically can still be missing a dependency that was never committed on either branch tip (happened here: `fal_vertical.py` existed only as an untracked working-tree file on one side, so the merge needed it added explicitly, flagged clearly to the user as a real gap rather than something invented).
