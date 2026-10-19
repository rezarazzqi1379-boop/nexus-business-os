"""EXPERIMENT_ONLY: explain hash false positives without changing Secret Guard.

No suppression, allowlist or handoff authorization. A digest is classified only
after recomputation from exact evidence bytes through a trusted blob reader.
All original findings remain in the report. Never relay matched token values.
"""
import hashlib
import json
import re

from contracts import canonical_digest
from coordination_kit import _SECRET_PATTERNS, scan_diff_for_secrets

SHA256 = re.compile(r"^[0-9a-f]{64}$")
SAFE_PATH = re.compile(r"^[A-Za-z0-9_./-]{1,240}$")


def verified_digests(payload, read_blob):
    proven = set()
    if not isinstance(payload, dict):
        return proven
    for field in ('file_manifest', 'evidence_hashes'):
        values = payload.get(field, {})
        if not isinstance(values, dict) or len(values) > 100:
            continue
        for path, digest in values.items():
            if not isinstance(path, str) or not SAFE_PATH.fullmatch(path):
                continue
            if path.startswith('/') or '..' in path.split('/') or any(
                part in {'.env', '.git', '.aws', '.codex'} for part in path.split('/')
            ):
                continue
            if field == 'evidence_hashes' and '/' not in path:
                path = 'data/research/' + path
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                continue
            try:
                body = read_blob(path)
            except Exception:
                continue
            if type(body) is bytes and len(body) <= 1_048_576 and hashlib.sha256(body).hexdigest() == digest:
                proven.add(digest)
    snapshot = payload.get('snapshot', {})
    events = snapshot.get('events', []) if isinstance(snapshot, dict) else []
    if not isinstance(events, list) or len(events) > 300:
        return proven
    for event in events:
        if not isinstance(event, dict) or not isinstance(event.get('body'), str) or len(event['body']) > 262144:
            continue
        try:
            record = json.loads(event['body'])
        except (ValueError, TypeError):
            continue
        if not isinstance(record, dict):
            continue
        if event.get('kind') == 'submitted' and isinstance(record.get('digest'), str):
            digest = record['digest']
            if SHA256.fullmatch(digest) and canonical_digest({k:v for k,v in record.items() if k != 'digest'}) == digest:
                proven.add(digest)
        docs = record.get('documents', [])
        if not isinstance(docs, list) or len(docs) > 10:
            continue
        for document in docs:
            if not isinstance(document, dict):
                continue
            body, digest = document.get('body'), document.get('sha256')
            if (isinstance(body, str) and len(body.encode('utf-8')) <= 65536 and
                isinstance(digest, str) and SHA256.fullmatch(digest) and
                hashlib.sha256(body.encode('utf-8')).hexdigest() == digest):
                proven.add(digest)
    return proven


def review_diff(diff_text, artifacts, read_blob):
    """Read-only diagnostic, deliberately incapable of returning ALLOW."""
    proven = set()
    for artifact in artifacts:
        proven.update(verified_digests(artifact, read_blob))
    matches = list(_SECRET_PATTERNS[6].finditer(diff_text))
    explained = sum(match.group() in proven for match in matches)
    findings = scan_diff_for_secrets(diff_text)
    return {'schema': 'nexus.evidence-digest-review.v1', 'mode': 'EXPERIMENT_ONLY',
            'original_findings': list(findings), 'generic_matches': len(matches),
            'recomputed_digest_matches': explained, 'unexplained_generic_matches': len(matches)-explained,
            'guard_decision': 'BLOCK' if findings else 'NO_FINDINGS',
            'suppressed_findings': 0, 'authorizes_handoff': False,
            'requires_security_review': True}
