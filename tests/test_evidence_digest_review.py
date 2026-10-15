import hashlib
import json

import pytest

from evidence_digest_review import review_diff, verified_digests
from coordination_kit import scan_diff_for_secrets


def test_recomputed_hash_explained_but_guard_still_blocks():
    body=b'public-source'
    digest=hashlib.sha256(body).hexdigest()
    diff=json.dumps({'sha256':digest})
    report=review_diff(diff,[{'file_manifest':{'source.txt':digest}}],lambda path:body)
    assert report['recomputed_digest_matches']==1
    assert report['guard_decision']=='BLOCK'
    assert report['suppressed_findings']==0 and not report['authorizes_handoff']
    assert scan_diff_for_secrets(diff)==('secret_pattern_6',)


@pytest.mark.parametrize('kind',['wrong_bytes','missing_blob','traversal','unknown_hex','credential_context'])
def test_no_credential_or_hash_bypass(kind):
    body=b'public-source'; digest=hashlib.sha256(body).hexdigest()
    path='../../.env' if kind=='traversal' else 'source.txt'
    def read(name):
        if kind=='missing_blob': raise FileNotFoundError()
        return b'other' if kind=='wrong_bytes' else body
    candidate='a'*64 if kind=='unknown_hex' else digest
    diff=json.dumps({'password' if kind=='credential_context' else 'sha256':candidate})
    report=review_diff(diff,[{'file_manifest':{path:digest}}],read)
    assert report['guard_decision']=='BLOCK' and not report['authorizes_handoff']
    if kind=='credential_context': assert 'secret_pattern_5' in report['original_findings']
    else: assert report['recomputed_digest_matches']==0


def test_embedded_body_tampering_not_explained():
    digest=hashlib.sha256(b'original').hexdigest()
    record={'documents':[{'body':'modified','sha256':digest}]}
    payload={'snapshot':{'events':[{'body':json.dumps(record),'kind':'checkpoint'}]}}
    assert not verified_digests(payload,lambda path:b'')


@pytest.mark.parametrize('prefix', ['sk-', 'AKIA', 'ghp_', 'xoxb-'])
def test_digest_does_not_certify_secret_free_body(prefix):
    # Deliberately synthetic credential shapes, never actual credentials.
    suffix='1'*16 if prefix=='AKIA' else 'A'*36
    body=prefix+suffix
    digest=hashlib.sha256(body.encode()).hexdigest()
    payload={'snapshot':{'events':[{'kind':'checkpoint','body':json.dumps({
        'documents':[{'body':body,'sha256':digest}]})}]}}
    report=review_diff(json.dumps(payload),[payload],lambda path:b'')
    assert report['recomputed_digest_matches']>=1
    assert report['guard_decision']=='BLOCK' and not report['authorizes_handoff']
    assert any(x!='secret_pattern_6' for x in report['original_findings'])


def test_recomputed_hash_in_password_context_still_blocks():
    body=b'public evidence'; digest=hashlib.sha256(body).hexdigest()
    report=review_diff(json.dumps({'password':digest}),[{'file_manifest':{'public.txt':digest}}],lambda path:body)
    assert report['recomputed_digest_matches']==1
    assert 'secret_pattern_5' in report['original_findings']
    assert report['guard_decision']=='BLOCK' and report['suppressed_findings']==0
