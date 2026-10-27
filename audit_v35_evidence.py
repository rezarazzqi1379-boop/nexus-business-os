"""Reproduce the 19 original hash findings against immutable original evidence.

No allowlist/suppression and no authorization. Does not print matched strings.
"""
from pathlib import Path
import hashlib
import json
import subprocess

from contracts import canonical_digest
from coordination_kit import _SECRET_PATTERNS
from evidence_digest_review import review_diff

ORIGINAL = '127edca49be8b0584019dd6acf683669135c89b5'
BASE = 'bd2568fc6bea59d2f8913b277cf012c925dfe584'


def audit(root):
    def blob(path):
        return subprocess.check_output(['git','show',ORIGINAL+':'+path],cwd=root)
    bindings=json.loads((root/'data/research/v32-original-byte-bindings.json').read_text())
    def original_bytes(path):
        if path in bindings:
            row=bindings[path]; canonical=blob(path)
            assert hashlib.sha256(canonical).hexdigest()==row['git_blob_sha256']
            indexes=set(row['crlf_line_indexes'])
            raw=b''.join(line[:-1]+b'\r\n' if i in indexes and line.endswith(b'\n') else line
                         for i,line in enumerate(canonical.splitlines(keepends=True)))
            assert hashlib.sha256(raw).hexdigest()==row['raw_sha256']
            return raw
        if path.startswith('data/research/'):
            # Exact preserved source bytes: its original verification manifest
            # checks each byte sequence, including PowerShell CRLF endings.
            return (root/path).read_bytes()
        return blob(path)
    names=['data/research/public-agent-live-2026-10-15.json',
           'data/research/public-agent-verification-2026-10-15.json']
    artifacts=[json.loads(original_bytes(path).decode('utf-8-sig')) for path in names]
    proofs={}
    for key,digest in artifacts[1]['file_manifest'].items():
        if hashlib.sha256(original_bytes(key)).hexdigest()==digest:
            proofs[digest]='file_manifest:'+key
    for key,digest in artifacts[1]['evidence_hashes'].items():
        if hashlib.sha256(original_bytes('data/research/'+key)).hexdigest()==digest:
            proofs[digest]='evidence_hashes:'+key
    for event in artifacts[0]['snapshot']['events']:
        record=json.loads(event['body'])
        if event['kind']=='submitted':
            digest=record['digest']
            assert canonical_digest({k:v for k,v in record.items() if k!='digest'})==digest
            proofs[digest]='canonical_submission_manifest:'+event['task']
        for doc in record.get('documents',[]):
            assert hashlib.sha256(doc['body'].encode()).hexdigest()==doc['sha256']
            proofs[doc['sha256']]='source_body:'+doc['url']
    diff=subprocess.check_output(['git','diff',BASE,ORIGINAL],cwd=root,text=True)
    report=review_diff(diff,artifacts,original_bytes)
    matches=list(_SECRET_PATTERNS[6].finditer(diff))
    report['occurrences']=[{'index':i,'length':len(m.group()),'provenance':proofs.get(m.group(),'UNEXPLAINED')}
                           for i,m in enumerate(matches)]
    report['original_commit']=ORIGINAL
    assert len(matches)==report['recomputed_digest_matches']==19
    assert report['guard_decision']=='BLOCK' and not report['authorizes_handoff']
    return report


if __name__=='__main__':
    root=Path(__file__).resolve().parent
    output=root/'data/research/v35-nineteen-finding-audit.json'
    output.write_text(json.dumps(audit(root),indent=2),encoding='utf-8')
    print('19/19 original occurrences verified; original guard still BLOCK')
