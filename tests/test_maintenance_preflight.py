import hashlib
import json

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
