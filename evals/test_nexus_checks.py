"""Regression tests: each test pins a real failure (ENGINEERING_FAILURE_MEMORY FM-005..FM-008)."""
import subprocess
from pathlib import Path

from nexus_checks import bilingual_parity, git_health, superseded_values, vendor_hygiene


def _w(tmp: Path, name: str, text: str) -> Path:
    p = tmp / name
    p.write_text(text, encoding="utf-8")
    return p


# ---- F14 vendor hygiene -------------------------------------------------
def test_f14_competitor_names_and_internal_pointer_are_caught(tmp_path):
    p = _w(tmp_path, "RFQ-X_EN.md",
           "# RFI\n## Suggested recipients\n- Nanjing Nianda Furnace\n"
           "- Fortune Electric (see internal QA log)\n")
    rules = {f.rule for f in vendor_hygiene.check_file(p)}
    assert {"F14-internal", "F14-name"} <= rules


def test_f14_clean_vendor_file_passes_but_banner_blocks_release(tmp_path):
    p = _w(tmp_path, "RFQ-X_EN.md",
           "**[DRAFT v5 — NOT APPROVED FOR RELEASE — delete this line only when releasing]**\n"
           "# Request for Information\nPlease state your legal name.\n")
    assert vendor_hygiene.check_file(p) == []
    assert [f.rule for f in vendor_hygiene.check_file(p, release=True)] == ["F14-banner"]


def test_f14_confusable_name_used_as_warning_is_still_caught(tmp_path):
    # v1-v3 kept "上海东方电气" inside a warning paragraph of the vendor file.
    p = _w(tmp_path, "RFQ-X_ZH.md", "注意：请勿与上海东方电气混淆。\n")
    assert any(f.rule == "F14-name" for f in vendor_hygiene.check_file(p))


# ---- F11 superseded values ----------------------------------------------
def test_f11_superseded_ratio_and_centre_are_errors(tmp_path):
    p = _w(tmp_path, "doc.md", "Recommended ratio 1:12.5 with pinion centre 618 mm.\n")
    rules = {f.rule for f in superseded_values.check_file(p)}
    assert {"SV-ratio-12.5", "SV-pinion-618"} <= rules


def test_f11_history_line_is_allowed(tmp_path):
    p = _w(tmp_path, "doc.md", "Ratio 1:12.5 (superseded) -> ~1:7.1\nنسبت ۱:۱۲٫۵ نسخهٔ پیشین\n")
    assert superseded_values.check_file(p) == []


def test_f11_persian_digits_are_normalised(tmp_path):
    p = _w(tmp_path, "doc.md", "وزن گیربکس ۸ تا ۱۶ تن\n")
    assert [f.rule for f in superseded_values.check_file(p)] == ["SV-gbx-weight-8-16"]


def test_reversal_238_only_when_not_described_as_accel_brake(tmp_path):
    bad = _w(tmp_path, "a.md", "Duty: up to 238 reversals per hour\n")
    ok = _w(tmp_path, "b.md", "85-170 reversals/h (accelerations plus brakings up to 238 per hour)\n")
    assert [f.rule for f in superseded_values.check_file(bad)] == ["SV-reversals-238"]
    assert superseded_values.check_file(ok) == []


def test_number_collision_1250kw_dc_is_not_flagged(tmp_path):
    # 1250 kW is BOTH the superseded AC motor and the engineer's DC spec (2026-09-23).
    dc = _w(tmp_path, "a.md", "Engineer spec: DC motor 1250 kW, gearbox 1:25\n")
    ac = _w(tmp_path, "b.md", "Main drive AC 1250 kW at 999 rpm\n")
    assert superseded_values.check_file(dc) == []
    assert [f.rule for f in superseded_values.check_file(ac)] == ["SV-ac-1250kW-999"]


# ---- F18 bilingual parity -------------------------------------------------
def test_f18_one_sided_edit_is_caught(tmp_path):
    en = _w(tmp_path, "RFQ-X_EN_v1.md", "## 1\n1. a\n2. b\n")
    zh = _w(tmp_path, "RFQ-X_ZH_v1.md", "## 1\n1. a\n2. b\n3. extra ask added only in ZH\n")
    f = bilingual_parity.check_paths([en, zh])
    assert f and f[0].rule == "F18-parity" and "numbered" in f[0].message


def test_f18_equal_structure_passes(tmp_path):
    en = _w(tmp_path, "RFQ-X_EN_v1.md", "## 1\n| a | b |\n|---|---|\n| 1 | 2 |\n")
    zh = _w(tmp_path, "RFQ-X_ZH_v1.md", "## 1\n| 甲 | 乙 |\n|---|---|\n| 1 | 2 |\n")
    assert bilingual_parity.check_paths([en, zh]) == []


# ---- F1 stale index after a plumbing commit ----------------------------------
def _git(repo, *a, env=None):
    return subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                          text=True, env=env).stdout.strip()


def test_f1_plumbing_commit_leaves_staged_deletions_and_is_detected(tmp_path):
    import os
    repo = tmp_path / "r"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@t"); _git(repo, "config", "user.name", "t")
    (repo / "a.md").write_text("a")
    _git(repo, "add", "a.md"); _git(repo, "commit", "-qm", "base")
    # Plumbing commit of a NEW file through a scratch index, as done on the bridge.
    (repo / "b.md").write_text("finished work")
    env = dict(os.environ, GIT_INDEX_FILE=str(tmp_path / "scratch_idx"))
    _git(repo, "read-tree", "HEAD", env=env)
    blob = _git(repo, "hash-object", "-w", "b.md")
    _git(repo, "update-index", "--add", "--cacheinfo", f"100644,{blob},b.md", env=env)
    tree = _git(repo, "write-tree", env=env)
    parent = _git(repo, "rev-parse", "HEAD")
    new = _git(repo, "commit-tree", tree, "-p", parent, "-m", "plumbing")
    _git(repo, "update-ref", "refs/heads/main", new, parent)
    f = git_health.check_repo(repo)
    stale = [x for x in f if x.rule == "F1-stale-index"]
    assert stale and stale[0].severity == "ERROR"      # b.md shows as staged deletion
    # Resync as the skill prescribes -> clean.
    env2 = dict(os.environ, GIT_INDEX_FILE=str(tmp_path / "resync_idx"))
    _git(repo, "read-tree", "HEAD", env=env2)
    (repo / ".git" / "index").write_bytes((tmp_path / "resync_idx").read_bytes())
    assert not [x for x in git_health.check_repo(repo) if x.rule == "F1-stale-index"]


def test_f2_live_lock_is_detected(tmp_path):
    repo = tmp_path / "r"; repo.mkdir()
    _git(repo, "init", "-q")
    (repo / ".git" / "index.lock").write_text("")
    assert any(x.rule == "F2-lock" for x in git_health.check_repo(repo))


def test_transition_line_mentioning_old_and_new_is_history(tmp_path):
    # Found by EXP-001 false-positive scan: "ratio moved from 1:12.5 to ~1:7.1".
    p = _w(tmp_path, "doc.md", "| 2026-09-21 | نسبت ترجیحی از ۱:۱۲٫۵ به ~۱:۷٫۱ |\n")
    assert superseded_values.check_file(p) == []
    q = _w(tmp_path, "doc2.md", "برآورد وزن گیربکس (۸–۱۶ تن) را کاملاً پس گرفت\n")
    assert superseded_values.check_file(q) == []


def test_cli_exclude_skips_archived_files(tmp_path, capsys):
    from nexus_checks.__main__ import main
    _w(tmp_path, "RFQ-OLD_EN_2026-09-22.md", "## Suggested recipients\n")
    _w(tmp_path, "RFQ-NEW_EN_v5.md", "## 1\nclean\n")
    assert main([str(tmp_path)]) == 1
    assert main([str(tmp_path), "--exclude", "*_2026-09-22.md"]) == 0
