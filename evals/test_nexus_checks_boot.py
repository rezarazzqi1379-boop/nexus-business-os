import subprocess
from pathlib import Path

from nexus_checks import boot


def _g(repo, *a):
    subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                   env={"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                        "GIT_COMMITTER_EMAIL": "t@t", "PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": str(repo)})


def _repo(tmp_path: Path) -> Path:
    r = tmp_path / "r"
    r.mkdir()
    _g(r, "init", "-q", "-b", "main")
    (r / "a.txt").write_text("x")
    _g(r, "add", "a.txt")
    _g(r, "commit", "-q", "-m", "base")
    return r


def test_finished_work_on_side_branch_is_found(tmp_path):
    r = _repo(tmp_path)
    _g(r, "checkout", "-q", "-b", "feat/steel-reroll-01")
    (r / "b.txt").write_text("y")
    _g(r, "add", "b.txt")
    _g(r, "commit", "-q", "-m", "reroll: Phase 1 for PRJ-STEEL-REROLL-01")
    _g(r, "checkout", "-q", "main")
    f = boot.check_repo(r, ["PRJ-STEEL-REROLL-01"])
    hits = [x.message for x in f if x.rule == "B5-project-hit"]
    assert any("feat/steel-reroll-01" in h and "1 unmerged commit" in h for h in hits)
    assert any(x.rule == "B2-local-only" and "feat/steel-reroll-01" in x.message for x in f)
    assert all(x.severity == "WARN" for x in f)


def test_no_hit_says_safe_to_start(tmp_path):
    r = _repo(tmp_path)
    f = boot.check_repo(r, ["PRJ-NOTHING-99"])
    assert [x.message for x in f if x.rule == "B5-project-hit"] == ["no unmerged work mentions 'PRJ-NOTHING-99': safe to start fresh"]


def test_merged_work_is_not_reported(tmp_path):
    r = _repo(tmp_path)
    _g(r, "checkout", "-q", "-b", "feat/done")
    (r / "c.txt").write_text("z")
    _g(r, "add", "c.txt")
    _g(r, "commit", "-q", "-m", "PRJ-DONE-01 finished")
    _g(r, "checkout", "-q", "main")
    _g(r, "merge", "-q", "--no-ff", "-m", "merge", "feat/done")
    hits = [x.message for x in boot.check_repo(r, ["PRJ-DONE-01"]) if x.rule == "B5-project-hit"]
    # the branch name does not contain the keyword and its commits are merged
    assert hits == ["no unmerged work mentions 'PRJ-DONE-01': safe to start fresh"]


def test_worktree_listed(tmp_path):
    r = _repo(tmp_path)
    wt = tmp_path / "wt"
    _g(r, "worktree", "add", "-q", "-b", "side", str(wt))
    assert any(x.rule == "B1-worktree" and "side" in x.message for x in boot.check_repo(r))
