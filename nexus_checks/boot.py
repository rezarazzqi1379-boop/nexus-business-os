"""Duplicate-work guard and resume digest (FM-013). Read-only, stdlib only.

Twice in two days a finished piece of work was redone because it sat on a local or
unmerged branch that the next session never looked at:
- 2026-09-29: the PRJ-STEEL-REROLL-01 study;
- 2026-09-30: the Constitution v4.0 audit.

A rule in CLAUDE.md was not enough, because the second session's checkout did not
even contain the rule. This module makes the check one command:

    python -m nexus_checks --boot --project PRJ-STEEL-REROLL-01 --project reroll

It reports WARN findings (never ERROR) so it can run anywhere, CI included:
- every worktree and its branch;
- local branches that are not on the remote (work that exists only here);
- remote branches ahead of main, newest first;
- PR heads not yet merged (via `git ls-remote`, which works where the REST API is blocked);
- for each --project keyword: every ref whose history mentions it, and branch names
  containing it. Any hit outside main means: resume that work, do not start over.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import Finding

CHECK = "boot"


def _git(repo: Path, *args: str, timeout: int = 60) -> str:
    try:
        r = subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args],
                           capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return r.stdout if r.returncode == 0 else ""


def _main_ref(repo: Path) -> str:
    for ref in ("origin/main", "main"):
        if _git(repo, "rev-parse", "-q", "--verify", ref).strip():
            return ref
    return "HEAD"


def worktrees(repo: Path) -> list[tuple[str, str]]:
    out, path = [], None
    for line in _git(repo, "worktree", "list", "--porcelain").splitlines():
        if line.startswith("worktree "):
            path = line[len("worktree "):]
        elif line.startswith("branch ") and path:
            out.append((path, line[len("branch refs/heads/"):]))
        elif line == "detached" and path:
            out.append((path, "(detached)"))
    return out


def local_only_branches(repo: Path) -> list[str]:
    remote = set(_git(repo, "for-each-ref", "--format=%(refname:strip=3)", "refs/remotes/origin").split())
    local = _git(repo, "for-each-ref", "--format=%(refname:strip=2)", "refs/heads").split()
    return [b for b in local if b not in remote]


def ahead_of_main(repo: Path, ref: str, main: str) -> int:
    n = _git(repo, "rev-list", "--count", f"{main}..{ref}").strip()
    return int(n) if n.isdigit() else 0


def open_pr_heads(repo: Path, main: str) -> list[tuple[str, str]]:
    out = []
    for line in _git(repo, "ls-remote", "origin", "refs/pull/*/head", timeout=30).splitlines():
        sha, ref = line.split("\t")
        num = ref.split("/")[2]
        # an unfetched head cannot be tested for ancestry; report it rather than guess
        known = _git(repo, "cat-file", "-t", sha).strip() == "commit"
        if not known:
            out.append((num, sha[:7] + " (not fetched)"))
            continue
        merged = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", sha, main],
                                capture_output=True).returncode == 0
        if not merged:
            out.append((num, sha[:7]))
    return sorted(out, key=lambda x: int(x[0]))


def project_hits(repo: Path, keyword: str, main: str) -> list[str]:
    """Refs (other than main) whose unmerged history mentions the keyword, plus branch names."""
    hits = []
    refs = _git(repo, "for-each-ref", "--format=%(refname:short)", "refs/heads", "refs/remotes").split()
    for ref in refs:
        if ref in (main, "origin/HEAD", "origin"):
            continue
        name_hit = keyword.lower() in ref.lower()
        log = _git(repo, "log", "--oneline", "-i", "--grep", keyword, f"{main}..{ref}")
        if name_hit or log.strip():
            n = len(log.strip().splitlines()) if log.strip() else 0
            last = _git(repo, "log", "-1", "--format=%cs %h %s", ref).strip()
            hits.append(f"{ref}: {n} unmerged commit(s) mention '{keyword}'"
                        f"{' (name match)' if name_hit else ''}; tip {last[:90]}")
    return hits


def check_repo(repo: Path, projects: list[str] | None = None) -> list[Finding]:
    repo = Path(repo)
    main = _main_ref(repo)
    f: list[Finding] = []

    def w(rule: str, msg: str) -> None:
        f.append(Finding(CHECK, "WARN", str(repo), 0, rule, msg))

    for path, br in worktrees(repo):
        w("B1-worktree", f"worktree {path} on {br}")
    for b in local_only_branches(repo):
        w("B2-local-only", f"branch '{b}' exists only locally ({ahead_of_main(repo, b, main)} commits ahead of {main}): push or archive it")
    rem = []
    for ref in _git(repo, "for-each-ref", "--sort=-committerdate", "--format=%(refname:short) %(committerdate:short)",
                    "refs/remotes/origin").splitlines():
        name = ref.split()[0]
        if name in ("origin/HEAD", "origin/main", "origin"):
            continue
        n = ahead_of_main(repo, name, main)
        if n:
            rem.append(f"{ref} (+{n})")
    for r in rem[:10]:
        w("B3-remote-ahead", f"remote branch ahead of {main}: {r}")
    prs = open_pr_heads(repo, main)
    for num, sha in prs[-6:]:  # newest numbers; git cannot tell open from closed-unmerged
        w("B4-open-pr", f"PR #{num} head {sha} is not merged into {main} (open, or closed without merge)")
    for kw in projects or []:
        hits = project_hits(repo, kw, main)
        if hits:
            for h in hits:
                w("B5-project-hit", h)
        else:
            w("B5-project-hit", f"no unmerged work mentions '{kw}': safe to start fresh")
    return f
