import hashlib
import json
import pytest

from maintenance_preflight import inventory_skills, check_pending_manifest


def test_duplicate_skill_drift_is_reported_not_reconciled(tmp_path):
    for name,content in [('a','one'),('b','two')]:
        directory=tmp_path/name; directory.mkdir()
        (directory/'SKILL.md').write_text('---\nname: shared\n---\n'+content)
    report=inventory_skills([tmp_path,tmp_path])
    assert len(report['skills'])==2
    assert report['collisions'][0]['content_drift']
    assert not report['automatic_changes']
    assert all(r['active']=='UNKNOWN' for r in report['skills'])


def test_inventory_bounds_and_missing_roots(tmp_path):
    for name in ['a','b']:
        directory=tmp_path/name; directory.mkdir()
        (directory/'SKILL.md').write_text('name: '+name)
    report=inventory_skills([tmp_path,tmp_path/'missing'],limit=1)
    assert len(report['skills'])==1 and report['coverage_truncated']
    assert report['missing_roots']


def test_manifest_drift_and_forged_approval_fail_closed(tmp_path):
    root=tmp_path/'data/research'; root.mkdir(parents=True)
    manifest=root/'v35-local-llm-manifest.json'; manifest.write_bytes(b'{}')
    approval=root/'v35-approval-request.json'
    approval.write_text(json.dumps({'manifest_sha256':hashlib.sha256(b'{}').hexdigest(),
                                    'status':'APPROVED','authorization_received':True}))
    assert not check_pending_manifest(tmp_path)['authorized']
    manifest.write_bytes(b'{"changed":true}')
    assert check_pending_manifest(tmp_path)['status']=='BLOCK_MANIFEST_DRIFT'


@pytest.mark.parametrize('kind',['malformed_approval','array_approval','malformed_manifest','oversized_manifest'])
def test_unusable_metadata_is_blocked_not_raised(tmp_path,kind):
    root=tmp_path/'data/research'; root.mkdir(parents=True)
    raw=b'{}'
    if kind=='malformed_manifest': raw=b'not-json'
    if kind=='oversized_manifest': raw=b' '*131073
    (root/'v35-local-llm-manifest.json').write_bytes(raw)
    approval=json.dumps({'manifest_sha256':hashlib.sha256(raw).hexdigest()})
    if kind=='malformed_approval': approval='not-json'
    if kind=='array_approval': approval='[]'
    (root/'v35-approval-request.json').write_text(approval)
    report=check_pending_manifest(tmp_path)
    assert report['status'].startswith('BLOCK_') and not report['authorized']


def test_unreadable_skill_does_not_hide_readable_siblings(tmp_path,monkeypatch):
    from pathlib import Path
    for name in ['bad','good']:
        directory=tmp_path/name; directory.mkdir()
        (directory/'SKILL.md').write_text('name: '+name)
    original=Path.open
    def open_file(path,*args,**kwargs):
        if path.parent.name=='bad': raise PermissionError('not public diagnostic text')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',open_file)
    report=inventory_skills([tmp_path])
    assert {r['status'] for r in report['skills']}=={'NOT_READ_IO_ERROR','FILE_PRESENT'}
    assert 'not public diagnostic text' not in str(report)


def test_oversized_skill_is_not_hashed_as_complete(tmp_path):
    (tmp_path/'SKILL.md').write_bytes(b'x'*131073)
    report=inventory_skills([tmp_path])
    assert report['skills'][0]['status']=='NOT_READ_SIZE_LIMIT'
    assert 'sha256' not in report['skills'][0]
