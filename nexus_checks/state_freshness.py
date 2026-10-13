"""State-file freshness and broken-pointer check.

Origin: the project's own continuity machinery had gone stale silently.
`.nexus/state/CURRENT_STATE.md` says "RULE: read this file first in any new
session" and last carried a timestamp from 2026-09-19, while
`docs/procurement/`, `docs/expert_foundry/` and `.nexus/steel/` had kept
moving for a week underneath it - exactly the "knowledge gets lost because
nobody re-reads the thing that changed" failure this repo's own state files
warn about (see `.nexus/steel/FRESHNESS_POLICY.yaml`: "STALE fara farz
nemishavad" - STALE is never assumed fresh).

Rule 1 (staleness): a governed state file is STALE when the newest git commit
touching any path it governs is more than `tolerance_days` newer than the
state file's own newest commit. The governing map lives in
`.nexus/state/STATE_GOVERNANCE.json` (JSON, not YAML: this repo has no YAML
parser as a dependency anywhere - `steel_kernel.py` hardcodes the same TTL
values in Python and treats its `.yaml` files as a human-readable mirror, not
something machine-parsed. This check is stdlib-only, so it follows that same
pattern instead of adding a YAML dependency for one file).

Rule 2 (broken pointers): the listed state/kernel files are scanned for
inline `` `backtick path` `` references that look like repo-relative paths;
a path that does not exist in the working tree is an ERROR. A dead pointer is
exactly how a reader gets silently routed to knowledge that no longer exists.

Both checks use `git log -1 --format=%ct -- <path>` (commit time, works for
both a single file and a directory - it returns the newest commit touching
anything under it) with `--no-optional-locks`, so this check never creates a
lock itself (same discipline as `git_health.py`, FM-008).
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from . import Finding

DEFAULT_CONFIG_PATH = Path(".nexus/state/STATE_GOVERNANCE.json")


def _git(repo: Path, *args: str) -> tuple[int, str]:
    p = subprocess.run(["git", "--no-optional-locks", "-C", str(repo), *args],
                       capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr).strip()


def _last_commit_time(repo: Path, path: str) -> int | None:
    """Newest commit time (unix seconds) touching `path`, file or directory. None if
    the path has no commit history reachable from HEAD (never committed, or the
    pathspec matches nothing)."""
    rc, out = _git(repo, "log", "-1", "--format=%ct", "--", path)
    if rc != 0 or not out:
        return None
    try:
        return int(out.splitlines()[0].strip())
    except ValueError:
        return None


def load_config(repo: Path, config_path: Path | None = None) -> dict:
    cfg_path = repo / (config_path or DEFAULT_CONFIG_PATH)
    if not cfg_path.exists():
        raise FileNotFoundError(
            f"no state-governance config at {cfg_path} - add one before relying on this check")
    return json.loads(cfg_path.read_text(encoding="utf-8"))


# A backtick span counts as a candidate repo-relative path reference only if it
# looks like one: has a path separator, no scheme/UNC/drive-letter/glob, no
# whitespace (which means it's prose or a shell command, not a bare path), and
# ends in a recognisable extension. This deliberately does NOT flag things like
# `C:/Users/AvallPc/nexus-business-os` (a real external machine path quoted as
# history, not a repo pointer) or `git log -1 --format=%ct -- path` (a command).
_BACKTICK = re.compile(r"`([^`\n]+)`")
_KNOWN_EXT = (".py", ".md", ".yaml", ".yml", ".json", ".txt", ".sh", ".ps1",
              ".xlsx", ".jsonl", ".toml", ".cfg", ".ini")
_BAD_SIGNS = ("://", "\\", " ", "*", "$", "<", ">", "|")


def _looks_like_repo_path(span: str) -> bool:
    if "/" not in span:
        return False
    if any(s in span for s in _BAD_SIGNS):
        return False
    if re.match(r"^[A-Za-z]:", span):          # drive letter, e.g. C:/Users/...
        return False
    if not span.lower().endswith(_KNOWN_EXT):
        return False
    if span.startswith(("/", "..")):
        return False
    return True


def _extract_path_refs(text: str) -> list[str]:
    out = []
    for span in _BACKTICK.findall(text):
        span = span.strip()
        if _looks_like_repo_path(span):
            out.append(span)
    return out


def check_repo(repo: Path, config_path: Path | None = None) -> list[Finding]:
    out: list[Finding] = []
    try:
        cfg = load_config(repo, config_path)
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return [Finding("state_freshness", "ERROR", str(config_path or DEFAULT_CONFIG_PATH), 0,
                        "SF-config", str(exc))]

    default_tolerance = int(cfg.get("tolerance_days", 0))

    # Rule 1: staleness.
    for entry in cfg.get("entries", []):
        state_file = entry["state_file"]
        tolerance_days = int(entry.get("tolerance_days", default_tolerance))
        tolerance_s = tolerance_days * 86400
        state_time = _last_commit_time(repo, state_file)
        if state_time is None:
            out.append(Finding("state_freshness", "WARN", state_file, 0, "SF-nohist",
                               "governed state file has no git history - cannot check freshness"))
            continue
        for governed in entry.get("governs", []):
            if not (repo / governed).exists():
                out.append(Finding("state_freshness", "WARN", state_file, 0, "SF-missing-governed-path",
                                   f"governs '{governed}', which does not exist in the tree - "
                                   "update STATE_GOVERNANCE.json"))
                continue
            governed_time = _last_commit_time(repo, governed)
            if governed_time is None:
                continue    # exists but never committed (e.g. untracked) - nothing to compare yet
            if governed_time > state_time + tolerance_s:
                age_days = (governed_time - state_time) / 86400
                out.append(Finding(
                    "state_freshness", "ERROR", state_file, 0, "SF-stale",
                    f"stale by ~{age_days:.1f}d: '{governed}' has commits newer than this "
                    f"state file's own last commit by more than the {tolerance_days}d tolerance"))

    # Rule 2: broken pointers in state/kernel files.
    for rel in cfg.get("broken_reference_scan", []):
        path = repo / rel
        if not path.exists():
            out.append(Finding("state_freshness", "ERROR", rel, 0, "SF-missing-scanned-file",
                               "listed in broken_reference_scan but does not exist"))
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.splitlines(), 1):
            for ref in _extract_path_refs(line):
                if not (repo / ref).exists():
                    out.append(Finding("state_freshness", "ERROR", rel, i, "SF-broken-ref",
                                       f"references '{ref}', which does not exist in the tree"))
    return out
