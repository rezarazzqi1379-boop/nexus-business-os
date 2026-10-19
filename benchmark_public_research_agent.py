"""Offline repeated evaluation against the saved real API payload, no network."""
import argparse
import json
from pathlib import Path
import statistics
import tempfile
from time import perf_counter

from nexus_public_research_agent import PublicResearchRuntime, URLS


def benchmark(capture):
    packet = json.loads(capture.read_text(encoding="utf-8-sig"))
    result = json.loads(next(e['body'] for e in packet['snapshot']['events'] if e['kind']=='checkpoint'))
    responses = {d['url']: d['body'].encode() for d in result['documents']}
    repo, release = [json.loads(responses[url]) for url in URLS]
    reference = {'full_name': repo['full_name'], 'archived': repo['archived'],
                 'pushed_at': repo['pushed_at'], 'license_spdx': repo['license']['spdx_id'],
                 'release_tag': release['tag_name'], 'release_published_at': release['published_at']}
    rows = []
    with tempfile.TemporaryDirectory() as directory:
        for i in range(10):
            calls = []
            def transport(url):
                calls.append(url)
                return responses[url]
            runtime = PublicResearchRuntime(Path(directory)/f'{i}.db', transport=transport)
            runtime.submit(f'frozen_{i}')
            started = perf_counter()
            assert runtime.drain() == 1
            elapsed = perf_counter()-started
            output = json.loads(next(e['body'] for e in runtime.snapshot()['events'] if e['kind']=='checkpoint'))
            matches = sum(output['values'][k] == v for k,v in reference.items())
            assert matches == 6 and runtime.review(f'frozen_{i}') == 'accepted'
            assert runtime.drain() == 0 and len(calls) == 2
            rows.append({'repeat': i, 'seconds': elapsed, 'field_matches': matches,
                         'expected_fields': 6, 'network_calls': 0, 'replay_execution': 0})
    return {'schema': 'nexus.public-agent-frozen-benchmark.v1', 'rows': rows,
            'median_seconds': statistics.median(row['seconds'] for row in rows),
            'accuracy_scope': 'schema extraction from saved payload, not independent truth',
            'model_calls': 0, 'model_tokens': 0, 'session_tokens': None}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(json.dumps(benchmark(args.capture), indent=2), encoding='utf-8')
