from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json

import pytest

import nexus_fts_source as fts
from nexus_router_runtime import PROJECT
from nexus_http_attempt_budget import AttemptBudget, AttemptBudgetExceeded

NOW = '2026-11-22T10:00:00+00:00'


def row(**updates):
    result = {'id': '012345-2026', 'ocid': 'ocds-h6vhtk-abc123', 'date': NOW,
              'tag': ['tender'], 'buyer': {'name': 'Public buyer CLAIM'},
              'tender': {'title': 'Industrial steel machinery', 'status': 'active',
                         'tenderPeriod': {'endDate': '2026-12-20T10:00:00Z'}}}
    result.update(updates)
    return result


def body(*rows):
    return json.dumps({'releases': list(rows)}).encode()


def test_missing_mandatory_evidence_never_promotes_keyword_match():
    item = fts.assess(body(row()), NOW)['assessments'][0]
    assert item['decision'] == 'INVESTIGATE' and item['keyword_relevance']
    assert set(item['verification_requirements'].values()) == {'UNKNOWN'}
    assert item['technical_specification_match'] == item['independent_technical_compatibility'] == 'UNKNOWN'
    assert not item['actionable'] and item['authority'] == 'HOLD'


@pytest.mark.parametrize('change,reason', [
    ({'date': '2025-01-01T00:00:00Z'}, 'stale_or_future_source'),
    ({'date': '2027-01-01T00:00:00Z'}, 'stale_or_future_source'),
    ({'tender': {'title': 'Steel', 'status': 'cancelled'}}, 'not_active_tender'),
    ({'tender': {'title': 'Steel', 'status': 'active', 'tenderPeriod': {'endDate': NOW}}}, 'deadline_missing_or_expired'),
    ({'tender': {'title': 'School services', 'status': 'active'}}, 'keyword_relevance_not_supported'),
])
def test_adverse_source_conditions_reject(change, reason):
    item = fts.assess(body(row(**change)), NOW)['assessments'][0]
    assert item['decision'] == 'REJECT' and reason in item['reasons']


def test_duplicates_and_conflicts_preserve_counts():
    first = row()
    other = row(buyer={'name': 'Conflicting buyer'})
    result = fts.assess(body(first, first, other), NOW)
    assert result['records_received'] == 3 and result['unique_records'] == 1
    assert result['duplicates_removed'] == 2 and result['decisions']['REJECT'] == 1
    assert 'conflicting_source_records' in result['assessments'][0]['reasons']
    assert sum(result['decisions'].values()) == result['unique_records']
    assert result == fts.assess(body(other, first, first), NOW)


@pytest.mark.parametrize('raw', [b'bad', b'[]', body(*[row()]*4), b'x'*(fts.MAX_BYTES+1),
    b'{"releases":[],"releases":[]}', body(row(date='2026-11-22T00:00:00')),
    body(row(id='../../unsafe')), body(row(buyer={'name': 'private@example.com'}))],
    ids=['malformed', 'root', 'rows', 'bytes', 'duplicate-key', 'naive', 'identity', 'private-text'])
def test_invalid_or_unsafe_sources_fail_closed(raw):
    with pytest.raises((ValueError, TypeError, KeyError)):
        fts.assess(raw, NOW)


def test_allowlist_and_live_budget_required(tmp_path):
    with pytest.raises(PermissionError):
        fts.fetch('https://127.0.0.1/private')
    with pytest.raises(ValueError, match='live_attempt_budget_required'):
        fts.FtsRuntime(tmp_path/'queue.db')


def test_existing_queue_supervisor_restart_replay_and_isolation(tmp_path):
    calls = []
    now = datetime.now(timezone.utc).isoformat()
    end = (datetime.now(timezone.utc)+timedelta(days=7)).isoformat()
    raw = body(row(date=now, tender={'title': 'Steel', 'status': 'active', 'tenderPeriod': {'endDate': end}}))
    runtime = fts.FtsRuntime(tmp_path/'queue.db', transport=lambda url: calls.append(url) or raw)
    assert runtime.submit('fts_acceptance', budget_units=3)
    assert runtime.drain(concurrency=3) == 1
    assert runtime.review('fts_acceptance') == 'accepted'
    replay = fts.FtsRuntime(tmp_path/'queue.db', transport=lambda _: pytest.fail('duplicate HTTP'))
    assert not replay.submit('fts_acceptance', budget_units=3)
    assert replay.drain(concurrency=3) == 0 and calls == [fts.SOURCE]
    with pytest.raises(PermissionError):
        replay.submit('cross_project', project_id='OTHER')
    with pytest.raises(PermissionError):
        replay.submit('no_authority', authority='ADMITTED')
    result = json.loads(next(x['body'] for x in replay.read_snapshot(tmp_path/'queue.db')['events']
                             if x['kind'] == 'checkpoint'))
    forged = deepcopy(result); forged['values']['commercially_verified'] = 1
    with pytest.raises(ValueError, match='inaccurate'):
        replay.validate_result({'task_id': 'fts_acceptance'}, forged)
    forged = deepcopy(result); forged['project_id'] = 'OTHER'
    with pytest.raises(ValueError, match='scope'):
        replay.validate_result({'task_id': 'fts_acceptance'}, forged)


def test_budget_survives_failed_transport_and_restart(tmp_path):
    path = tmp_path/'queue.db.http-attempts.sqlite'
    budget = AttemptBudget(path, scope='nexus:fts:bounded-read', max_attempts=1)
    def fail(_):
        raise RuntimeError('private provider error')
    with pytest.raises(RuntimeError):
        budget.read('task', fail, fts.SOURCE)
    again = AttemptBudget(path, scope='nexus:fts:bounded-read', max_attempts=1)
    with pytest.raises(AttemptBudgetExceeded):
        again.read('task', lambda _: pytest.fail('budget bypass'), fts.SOURCE)


def test_connector_failure_is_redacted_and_queue_recovers_safely(tmp_path):
    runtime = fts.FtsRuntime(tmp_path/'queue.db', transport=lambda _: (_ for _ in ()).throw(RuntimeError('secret=private')))
    runtime.submit('failed_source', budget_units=3)
    assert runtime.drain(concurrency=1) == 0
    snapshot = runtime.read_snapshot(tmp_path/'queue.db')
    assert 'private' not in json.dumps(snapshot)
    assert any(x['kind'] == 'failed' for x in snapshot['events'])


def test_source_mode_and_ledger_binding_cannot_change_on_restart(tmp_path):
    path = tmp_path/'queue.db'
    budget = AttemptBudget(str(path)+'.http-attempts.sqlite', scope='nexus:fts:bounded-read', max_attempts=1)
    fts.FtsRuntime(path, transport=lambda _: body())
    with pytest.raises(ValueError, match='source_binding_requires_recovery'):
        fts.FtsRuntime(path, attempt_budget=budget)


@pytest.mark.parametrize('status,content_type', [(302,'application/json'),(429,'application/json'),(200,'text/html')])
def test_http_failure_is_not_retried_or_followed(monkeypatch, status, content_type):
    requests=[]
    class Connection:
        def __init__(self, *args, **kwargs):
            pass
        def request(self, method, path, headers):
            requests.append((method,path))
        def getresponse(self):
            return self
        def getheader(self, name, default=''):
            return content_type
        def close(self):
            pass
    Connection.status=status
    monkeypatch.setattr(fts.http.client,'HTTPSConnection',Connection)
    with pytest.raises(fts.AcquisitionError,match='bounded_source_read_failed'):
        fts.fetch(fts.SOURCE)
    assert len(requests)==1 and requests[0][0]=='GET'
