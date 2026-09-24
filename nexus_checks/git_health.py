"""Git repository health for bridged / plumbing-committed repos.

Origin (FM-008; audit F1, F2, F3): commits made with git plumbing on a
bridged Windows mount left the real .git/index behind HEAD, so 18 files of
finished work sat "staged for deletion" - one ordinary `git commit` (or an
auto-commit hook) would have deleted them. Live HEAD.lock / index.lock files
blocked the owner's own git, and the work branch had never been pushed.

All git calls use --no-optional-locks so this check never creates a lock itself.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

from . import Finding


def _git(repo: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def check_repo(repo: Path) -> list[Finding]:
    out: list[Finding] = []
    gitdir = repo / ".git"
    for lock in ["index.lock", "HEAD.lock"]:
        if (gitdir / lock).exists():
            out.append(Finding("git_health", "ERROR", str(gitdir / lock), 0, "F2-lock",
                               "live lock file: owner's git will refuse to work"))
    for lock in gitdir.glob("refs/heads/**/*.lock"):
        out.append(Finding("git_health", "ERROR", str(lock), 0, "F2-lock", "live ref lock"))

    rc, staged = _git(repo, "diff", "--cached", "--name-status")
    if rc == 0 and staged:
        deletions = [l for l in staged.splitlines() if l.startswith("D")]
        sev = "ERROR" if deletions else "WARN"
        out.append(Finding("git_health", sev, str(repo), 0, "F1-stale-index",
                           f"{len(staged.splitlines())} staged change(s) vs HEAD, "
                           f"{len(deletions)} deletion(s): if not intended, the index "
                           "is stale after a plumbing commit - resync before any commit"))

    rc, up = _git(repo, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if rc != 0:
        out.append(Finding("git_health", "WARN", str(repo), 0, "F3-no-upstream",
                           "current branch has no upstream: work exists only locally"))
    else:
        rc, ahead = _git(repo, "rev-list", "--count", "@{u}..HEAD")
        if rc == 0 and ahead.isdigit() and int(ahead) > 0:
            out.append(Finding("git_health", "WARN", str(repo), 0, "F3-unpushed",
                               f"{ahead} commit(s) not pushed to {up}"))
    return out
