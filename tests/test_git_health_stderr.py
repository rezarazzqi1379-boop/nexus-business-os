import subprocess
from nexus_checks.git_health import _git


def test_successful_git_data_excludes_environment_warning(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw:
                        subprocess.CompletedProcess(a, 0, "", "warning: ignore permission denied"))
    assert _git(tmp_path, "diff", "--cached") == (0, "")


def test_failed_git_query_retains_diagnostic(monkeypatch, tmp_path):
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw:
                        subprocess.CompletedProcess(a, 128, "", "fatal: no repository"))
    assert _git(tmp_path, "rev-parse", "HEAD") == (128, "fatal: no repository")
