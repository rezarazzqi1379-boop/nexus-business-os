import json

import pytest

from nexus_free_research import run
from nexus_public_research_agent import PublicResearchRuntime, REPO, URLS


def transport(calls):
    bodies = [json.dumps({"full_name": REPO, "archived": False,
        "pushed_at": "2026-01-01T00:00:00Z", "license": {"spdx_id": "MIT"},
        "private_extra": "MUST_NOT_EXPORT_RESPONSE_BODY"}).encode(),
        json.dumps({"html_url": f"https://github.com/{REPO}/releases/tag/v1",
                    "tag_name": "v1", "published_at": "2026-01-01T00:00:00Z"}).encode()]
    def fetch(url):
        calls.append(url)
        return bodies[URLS.index(url)]
    return fetch


def test_one_task_checkpoint_supervision_restart_and_dedup_are_verified():
    calls = []
    summary = run(transport=transport(calls))
    assert summary['status'] == 'VERIFIED'
    assert summary['source_mode'] == 'FROZEN_TEST_FIXTURE'
    assert summary['tasks_completed'] == 1 and calls == list(URLS)
    assert summary['supervisor'] == 'accepted' and summary['checkpoint_integrity']
    assert summary['duplicate_execution_prevented']
    assert summary['http_reads_attempted'] == summary['http_read_budget'] == 2
    assert not summary['authority_promoted'] and summary['external_writes'] == 0
    serialized = json.dumps(summary)
    assert 'MUST_NOT_EXPORT' not in serialized
    assert 'body' not in serialized and 'queue.db' not in serialized


def test_external_failure_is_blocked_and_redacted():
    def failure(url):
        raise RuntimeError('PRIVATE_PROVIDER_MESSAGE')
    summary = run(transport=failure)
    assert summary['status'] == 'BLOCKED' and summary['tasks_completed'] == 0
    assert summary['http_reads_attempted'] == 1
    assert 'PRIVATE_PROVIDER_MESSAGE' not in json.dumps(summary)
    assert 'sources' not in summary


def test_supervisor_rejection_cannot_be_reported_verified(monkeypatch):
    monkeypatch.setattr(PublicResearchRuntime, 'review', lambda *args: 'rejected')
    summary = run(transport=transport([]))
    assert summary['status'] == 'BLOCKED' and summary['tasks_completed'] == 0


def test_real_source_submission_is_never_labelled_synthetic(tmp_path):
    runtime = PublicResearchRuntime(tmp_path / 'queue.db', transport=transport([]))
    runtime.submit('bounded', budget_units=3)
    submission = json.loads(next(e['body'] for e in runtime.snapshot()['events'] if e['kind'] == 'submitted'))
    assert submission['authority'] == 'UNVERIFIED_PUBLIC'
    with pytest.raises(PermissionError):
        runtime.submit('blocked', authority='CANONICAL')


def test_cli_failure_exit_and_summary_have_no_raw_exception(tmp_path, monkeypatch, capsys):
    import nexus_free_research as module
    monkeypatch.setattr(module, 'public_get', lambda url: (_ for _ in ()).throw(RuntimeError('DO_NOT_LOG')))
    output = tmp_path / 'summary.json'
    monkeypatch.setattr('sys.argv', ['nexus_free_research', '--summary', str(output)])
    assert module.main() == 1
    assert json.loads(output.read_text())['source_mode'] == 'REAL_PUBLIC_HTTP'
    assert 'DO_NOT_LOG' not in capsys.readouterr().out
