"""Record the observed corrected trajectory; do not promote it as clean learning."""
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo))
sys.path.insert(0, str(repo / 'src'))
from self_improvement_runtime import SystemExercise, run_self_improvement_cycle, record_cycle
from unified_data_environment import UnifiedDataHub
from nexus_core.project_memory import ProjectMemoryStore

now = datetime.now(timezone.utc).isoformat()
exercise = SystemExercise('intelligence-install-2026-10-08', 'intelligence-platform',
    'SANDBOX', 'incremental-install', 'incremental-evidence',
    ('docs/research/NEXUS_INTELLIGENCE_RUNTIME_2026-10-08.md',
     'data/research/intelligence-runtime-proof.json', 'data/research/intelligence-live-proof.json'),
    ('pinned install', 'dependency review', 'restart probe', 'correct measurement and observation IDs'),
    ('python tools/probe_intelligence_runtime.py', 'python tools/probe_intelligence_source.py',
     'PYTHONPATH=src PYTHONUTF8=1 python -m pytest -q tests evals'),
    ('repeat emits zero', 'cross-project rejected', 'lineage preserved'),
    'PARTIAL', 0, (), now)
report = run_self_improvement_cycle((exercise,), project_id='SANDBOX', rollback_ref='884e2f0')
hub = UnifiedDataHub(repo / 'data/nexus_system/unified_data_hub.db', repo)
record_cycle(hub, report, now)
(repo / 'data/research/intelligence-self-use.json').write_text(json.dumps(asdict(report), indent=2), encoding='utf-8')
memory = ProjectMemoryStore(repo / '.nexus/memory')
memory.record('context', 'Intelligence sandbox installed with pinned dlt; restart/dedupe and scope probes pass. Existing daily heartbeat updated; next scheduled execution unobserved. Canonical v1.8/v2.1 binaries remain missing. No clean-learning or commercial promotion.',
              decided_by='Codex observed execution', project_id='SANDBOX', lane='technology-proof',
              evidence_refs=('docs/research/NEXUS_INTELLIGENCE_RUNTIME_2026-10-08.md',),
              entry_id='context-intelligence-2026-10-08')
print(json.dumps(asdict(report)))
