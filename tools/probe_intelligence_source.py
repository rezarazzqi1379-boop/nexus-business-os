"""One bounded public metadata read -> dlt claims -> existing graph and hub."""
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from urllib.request import Request, urlopen

os.environ['RUNTIME__DLTHUB_TELEMETRY'] = 'false'
repo = Path(__file__).resolve().parents[1]
os.environ['DLT_DATA_DIR'] = str(repo / '.nexus/intelligence-runtime/dlt')
sys.path.insert(0, str(repo))
from intelligence_dlt_adapter import load_scoped_records, verify_runtime_lock
from intelligence_graph import Node, link
from unified_data_environment import UnifiedDataHub, EvidenceObservation


def run():
    verify_runtime_lock(repo / 'config/intelligence-runtime.lock.txt')
    url = 'https://pypi.org/pypi/dlt/1.31.0/json'
    with urlopen(Request(url, headers={'User-Agent': 'NEXUS-bounded-metadata-proof/1'}), timeout=20) as response:
        payload = response.read(2_000_001)
    if len(payload) > 2_000_000:
        raise ValueError('source_byte_budget_exceeded')
    metadata = json.loads(payload)['info']
    if metadata['name'] != 'dlt' or metadata['version'] != '1.31.0':
        raise ValueError('unexpected_package_identity')
    digest = sha256(payload).hexdigest()
    now = datetime.now(timezone.utc)
    root = repo / '.nexus/intelligence-runtime'
    root.mkdir(parents=True, exist_ok=True)
    # Stable cursor per content revision; timestamp of this read is separately recorded.
    stamp = root / f'pypi-{digest}.json'
    cursor = json.loads(stamp.read_text(encoding='utf-8'))['cursor'] if stamp.exists() else int(now.timestamp() * 1_000_000)
    row = dict(id='pypi-dlt-1.31.0', project_id='SANDBOX', lane='technology-proof',
               source_ref=url, origin_id='pypi:dlt:1.31.0', evidence_class='CLAIM',
               updated_at=cursor, content_sha256=digest,
               license_claim=metadata.get('license_expression') or metadata.get('license') or 'UNKNOWN')
    loaded = load_scoped_records([row], project_id='SANDBOX', lane='technology-proof', root=root)
    stamp.write_text(json.dumps({'cursor': cursor}), encoding='utf-8')
    ref = f'{url}#sha256={digest}'
    package = Node('dlt:1.31.0', 'PACKAGE', 'SANDBOX', now.isoformat(), ref, 'CLAIM')
    license_node = Node(row['license_claim'], 'LICENSE', 'SANDBOX', now.isoformat(), ref, 'CLAIM')
    edge = link(package, license_node, 'DECLARES_LICENSE', ref)
    result = dict(observed_at=now.isoformat(), source=url, bytes_read=len(payload),
                  content_sha256=digest, loading=loaded, edge=asdict(edge),
                  model_calls=0, queries=1, commercial_outcome='UNPROVEN')
    proof = repo / 'data/research/intelligence-live-proof.json'
    proof.write_text(json.dumps(result, indent=2), encoding='utf-8')
    observation_id = 'intelligence-' + sha256((digest + now.isoformat()).encode()).hexdigest()[:24]
    snapshot = root / (observation_id + '.json')
    snapshot.write_text(json.dumps(result, indent=2), encoding='utf-8')
    hub = UnifiedDataHub(repo / 'data/nexus_system/unified_data_hub.db', repo)
    hub.record_observation(EvidenceObservation(observation_id, 'SANDBOX',
        'TECHNOLOGY_METADATA_CLAIM', 'Public pinned package metadata acquired; commercial outcome unproven.',
        (ref, snapshot.relative_to(repo).as_posix()), now.isoformat(), 0.5))
    print(json.dumps(result))


if __name__ == '__main__':
    run()
