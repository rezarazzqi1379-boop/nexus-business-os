"""Verify downloaded public pilot artifact bytes without extracting ZIP paths."""
import argparse
import hashlib
from io import BytesIO
import json
import math
from pathlib import Path
import sys
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from nexus_commercial_pilot import assess, management_report


def verify_archive(blob, expected_digest, expected_commit, *, assessor=assess, reporter=management_report,
                   legacy_float_tolerance=False):
    if len(blob) > 262144 or hashlib.sha256(blob).hexdigest() != expected_digest.removeprefix('sha256:'):
        raise ValueError('archive_digest_or_size_mismatch')
    with zipfile.ZipFile(BytesIO(blob)) as archive:
        names = archive.namelist()
        if sorted(names) != ['management-fa.md', 'public-source.json', 'summary.json']:
            raise ValueError('unexpected_archive_members')
        if any(i.file_size > 131072 or i.flag_bits & 1 for i in archive.infolist()):
            raise ValueError('unsafe_archive_member')
        summary = json.loads(archive.read('summary.json'))
        source = archive.read('public-source.json')
        report = archive.read('management-fa.md').decode('utf-8')
    if summary['commit_sha'] != expected_commit or summary['status'] != 'VERIFIED' or summary['source_mode'] != 'REAL_PUBLIC_HTTP':
        raise ValueError('execution_binding_mismatch')
    if hashlib.sha256(source).hexdigest() != summary['source_sha256']:
        raise ValueError('source_digest_mismatch')
    def same(actual, expected):
        if isinstance(actual, dict) and isinstance(expected, dict):
            return actual.keys() == expected.keys() and all(same(actual[k], expected[k]) for k in expected)
        if isinstance(actual, list) and isinstance(expected, list):
            return len(actual) == len(expected) and all(same(a,b) for a,b in zip(actual, expected))
        if legacy_float_tolerance and type(actual) is float and type(expected) is float:
            return math.isfinite(actual) and math.isfinite(expected) and math.isclose(actual,expected,rel_tol=0,abs_tol=1e-12)
        return type(actual) is type(expected) and actual == expected
    for key, value in assessor(source, summary['source_retrieved_at']).items():
        if not same(summary.get(key), value):
            raise ValueError('assessment_mismatch')
    if report != reporter(summary):
        raise ValueError('report_mismatch')
    if summary['external_writes'] != 0 or summary['authority_status'] != 'HOLD' or summary['http_requests'] != 1:
        raise ValueError('safety_metrics_mismatch')
    return {'status':'VERIFIED','commit_sha':expected_commit,'archive_sha256':hashlib.sha256(blob).hexdigest(),
        'source_sha256':summary['source_sha256'],'source_bytes':len(source),
        'assessment_reproduced':True,'persian_report_reproduced':True,
        'legacy_float_tolerance':1e-12 if legacy_float_tolerance else 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--commit', required=True)
    args = parser.parse_args()
    print(json.dumps(verify_archive(args.archive.read_bytes(), args.sha256, args.commit)))
