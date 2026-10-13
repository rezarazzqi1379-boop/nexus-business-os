"""Regression tests for nexus_checks.state_freshness (temp git repos, no network).

Covers: fresh state passes, a governed path with a newer commit than the state
file fails (SF-stale), and a broken `backtick path` reference in a scanned
state/kernel file fails (SF-broken-ref).
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from nexus_checks import state_freshness


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def _init_repo(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t")
    _git(repo, "config", "user.name", "t")


def _commit_all(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)


def _write(repo: Path, rel: str, text: str) -> Path:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _config(*, tolerance_days=2, entries=None, scan=None) -> dict:
    return {
        "version": 1,
        "tolerance_days": tolerance_days,
        "entries": entries if entries is not None else [
            {"state_file": "STATE.md", "governs": ["docs"]},
        ],
        "broken_reference_scan": scan if scan is not None else ["STATE.md"],
    }


def _write_config(repo: Path, cfg: dict) -> None:
    _write(repo, ".nexus/state/STATE_GOVERNANCE.json", json.dumps(cfg))


# ---- Rule 1: staleness ------------------------------------------------------

def test_fresh_state_passes(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write(repo, "STATE.md", "# state\ncurrent as of this commit\n")
    _write_config(repo, _config())
    _commit_all(repo, "initial: docs and state together")

    findings = state_freshness.check_repo(repo)
    assert [f for f in findings if f.rule == "SF-stale"] == []


def test_governed_path_newer_than_state_file_is_stale(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write(repo, "STATE.md", "# state\n")
    _write_config(repo, _config(tolerance_days=0))
    _commit_all(repo, "initial")

    # A later commit touches only the governed path, not the state file.
    time.sleep(1.1)   # git commit time has 1s resolution
    _write(repo, "docs/a.md", "hello, updated")
    _commit_all(repo, "docs changed, state file NOT updated")

    findings = state_freshness.check_repo(repo)
    stale = [f for f in findings if f.rule == "SF-stale"]
    assert stale and stale[0].severity == "ERROR"
    assert stale[0].path == "STATE.md"


def test_tolerance_absorbs_a_small_gap(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write(repo, "STATE.md", "# state\n")
    _write_config(repo, _config(tolerance_days=2))
    _commit_all(repo, "initial")

    time.sleep(1.1)
    _write(repo, "docs/a.md", "hello, updated")
    _commit_all(repo, "docs changed, well within the 2-day tolerance")

    findings = state_freshness.check_repo(repo)
    assert [f for f in findings if f.rule == "SF-stale"] == []


def test_state_file_updated_after_governed_path_is_fresh_again(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write(repo, "STATE.md", "# state v1\n")
    _write_config(repo, _config(tolerance_days=0))
    _commit_all(repo, "initial")

    time.sleep(1.1)
    _write(repo, "docs/a.md", "hello, updated")
    _commit_all(repo, "docs changed")

    time.sleep(1.1)
    _write(repo, "STATE.md", "# state v2 - reflects the docs change\n")
    _commit_all(repo, "state file caught up")

    findings = state_freshness.check_repo(repo)
    assert [f for f in findings if f.rule == "SF-stale"] == []


def test_missing_governed_path_warns_not_errors(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "STATE.md", "# state\n")
    _write_config(repo, _config(entries=[
        {"state_file": "STATE.md", "governs": ["docs/does_not_exist"]},
    ]))
    _commit_all(repo, "initial")

    findings = state_freshness.check_repo(repo)
    missing = [f for f in findings if f.rule == "SF-missing-governed-path"]
    assert missing and missing[0].severity == "WARN"
    assert [f for f in findings if f.rule == "SF-stale"] == []


def test_state_file_with_no_history_warns(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write_config(repo, _config(entries=[
        {"state_file": "NEVER_COMMITTED.md", "governs": ["docs"]},
    ]))
    _commit_all(repo, "initial, without the state file")

    findings = state_freshness.check_repo(repo)
    assert any(f.rule == "SF-nohist" and f.severity == "WARN" for f in findings)


# ---- Rule 2: broken pointers ------------------------------------------------

def test_broken_path_reference_is_caught(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "STATE.md",
           "See `docs/real.md` for details.\n"
           "Also see `docs/ghost.md`, which was deleted last week.\n")
    _write(repo, "docs/real.md", "still here")
    _write_config(repo, _config(entries=[], scan=["STATE.md"]))
    _commit_all(repo, "initial")

    findings = state_freshness.check_repo(repo)
    broken = [f for f in findings if f.rule == "SF-broken-ref"]
    assert len(broken) == 1
    assert "docs/ghost.md" in broken[0].message
    assert broken[0].line == 2


def test_non_path_backtick_spans_are_not_flagged(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "STATE.md",
           "Clone A: `C:/Users/AvallPc/nexus-business-os` (external machine, not a repo path).\n"
           "Run `git log -1 --format=%ct -- path` to check.\n"
           "Function `steel_kernel.freshness_of` is not a file path.\n"
           "`docs/real.md` does exist.\n")
    _write(repo, "docs/real.md", "still here")
    _write_config(repo, _config(entries=[], scan=["STATE.md"]))
    _commit_all(repo, "initial")

    findings = state_freshness.check_repo(repo)
    assert [f for f in findings if f.rule == "SF-broken-ref"] == []


def test_missing_scanned_file_is_an_error(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write_config(repo, _config(entries=[], scan=["NOPE.md"]))
    _commit_all(repo, "initial")

    findings = state_freshness.check_repo(repo)
    assert any(f.rule == "SF-missing-scanned-file" and f.severity == "ERROR" for f in findings)


# ---- config errors -----------------------------------------------------------

def test_missing_config_is_reported_not_raised(tmp_path):
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _commit_all(repo, "initial, no STATE_GOVERNANCE.json")

    findings = state_freshness.check_repo(repo)
    assert findings and findings[0].rule == "SF-config"


def test_cli_state_flag_runs_the_check(tmp_path, capsys):
    from nexus_checks.__main__ import main
    repo = tmp_path / "r"
    _init_repo(repo)
    _write(repo, "docs/a.md", "hello")
    _write(repo, "STATE.md", "# state\n")
    _write_config(repo, _config(tolerance_days=0))
    _commit_all(repo, "initial")

    time.sleep(1.1)
    _write(repo, "docs/a.md", "hello, updated")
    _commit_all(repo, "docs changed, state file NOT updated")

    assert main(["--state", "--repo", str(repo)]) == 1
    out = capsys.readouterr().out
    assert "SF-stale" in out
