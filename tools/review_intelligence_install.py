"""Freeze the pip plan and query OSV without installing any package."""
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

plan = json.loads(Path('data/research/intelligence-install-plan.json').read_text(encoding='utf-8'))
packages = plan['install']
lines = []
queries = []
for item in packages:
    name, version = item['metadata']['name'], item['metadata']['version']
    digest = item['download_info']['archive_info']['hashes']['sha256']
    lines.append(f'{name}=={version} --hash=sha256:{digest}')
    queries.append({'package': {'name': name, 'ecosystem': 'PyPI'}, 'version': version})
Path('config/intelligence-runtime.lock.txt').write_text('\n'.join(sorted(lines)) + '\n', encoding='utf-8')
report = {'packages': [{'name': q['package']['name'], 'version': q['version']} for q in queries],
          'source': 'https://api.osv.dev/v1/querybatch', 'state': 'UNKNOWN',
          'observed_at': datetime.now(timezone.utc).isoformat()}
try:
    req = Request(report['source'], data=json.dumps({'queries': queries}).encode(),
                  headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=30) as response:
        result = json.load(response)
    report['results'] = result['results']
    report['state'] = 'KNOWN_ADVISORIES' if any(r.get('vulns') for r in result['results']) else 'NO_KNOWN_ADVISORIES_IN_OSV'
except Exception as exc:
    report['error_type'] = type(exc).__name__
Path('data/research/intelligence-dependency-review.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'packages': len(queries), 'security_state': report['state']}))
