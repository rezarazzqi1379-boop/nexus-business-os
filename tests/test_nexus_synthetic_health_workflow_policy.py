"""Regression checks for the opt-in, synthetic-only health workflow.

These are policy assertions about repository code, not proof of a live schedule.
"""
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "nexus-synthetic-health.yml"

def test_workflow_is_explicitly_read_only():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "contents: read" in text
    assert "runs-on: ubuntu-latest" in text
    assert "timeout-minutes: 5" in text
    assert "workflow_dispatch:" in text
    assert "schedule:" in text

def test_workflow_does_not_use_secrets_or_external_deploy():
    text = WORKFLOW.read_text(encoding="utf-8").lower()
    for forbidden in ("secrets.", "self-hosted", "deploy", "docker login", "curl ", "wget ", "write-all", "pull_request_target"):
        assert forbidden not in text

def test_workflow_checks_for_false_activation_claims():
    text = WORKFLOW.read_text(encoding="utf-8")
    for expected in ('report["ci_checks_passed"]', 'report["local_install_verified"]',
                     'report["persistent_service_verified"]', 'report["production_ready"]'):
        assert expected in text

def test_workflow_only_has_readonly_health_command():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "from nexus_lab_health import self_test" in text
    assert "pip install" not in text
    assert "git push" not in text
