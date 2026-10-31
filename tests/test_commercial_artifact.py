"""Frozen artifact fixtures; no network or live business evidence."""
from hashlib import sha256
from io import BytesIO
import json
import zipfile

import pytest

from nexus_commercial_pilot import assess, management_report
from scripts.verify_commercial_artifact import verify_archive


def archive(*, change=None):
    source = b'{"rows":0,"os":"0","page":"1","total":"0","procnotices":[]}'
    summary = {**assess(source, '2026-10-31T10:00:00+00:00'),
        'commit_sha':'a'*40,'status':'VERIFIED','source_mode':'REAL_PUBLIC_HTTP',
        'source_retrieved_at':'2026-10-31T10:00:00+00:00','source_sha256':sha256(source).hexdigest(),
        'external_writes':0,'http_requests':1}
    members={'summary.json':json.dumps(summary).encode(),'public-source.json':source,
             'management-fa.md':management_report(summary).encode()}
    if change: change(members)
    out=BytesIO()
    with zipfile.ZipFile(out,'w') as z:
        for name,value in members.items(): z.writestr(name,value)
    return out.getvalue()


def test_exact_artifact_bytes_and_report_reproduce():
    blob=archive()
    result=verify_archive(blob,sha256(blob).hexdigest(),'a'*40)
    assert result['assessment_reproduced'] and result['persian_report_reproduced']
    assert result['legacy_float_tolerance']==0


@pytest.mark.parametrize('kind',['archive_hash','commit','source','report','path','assessment'])
def test_corrupt_or_misbound_artifact_is_rejected(kind):
    def change(m):
        if kind=='source': m['public-source.json']+=b' '
        elif kind=='report': m['management-fa.md']=b'forged'
        elif kind=='path': m['../escape']=b'bad'
        elif kind=='assessment':
            d=json.loads(m['summary.json']);d['opportunities_verified']=1
            m['summary.json']=json.dumps(d).encode()
    blob=archive(change=change)
    with pytest.raises(ValueError):
        verify_archive(blob,'0'*64 if kind=='archive_hash' else sha256(blob).hexdigest(),
                       'b'*40 if kind=='commit' else 'a'*40)
