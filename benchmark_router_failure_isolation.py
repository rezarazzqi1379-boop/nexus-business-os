"""Paired fault-injection comparison against immutable pre-fix router code.

Only trusted local Git source is loaded. No providers, credentials or network.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
from time import perf_counter

from nexus_router_runtime import SyntheticRuntime

BASELINE='690b9c84c21f7380f51345d34e63726578a3cb77'


def benchmark(root):
    source=subprocess.check_output(['git','show',BASELINE+':nexus_router_runtime.py'],cwd=root)
    rows=[]
    with tempfile.TemporaryDirectory() as directory:
        directory=Path(directory); file=directory/'baseline_router.py'; file.write_bytes(source)
        spec=importlib.util.spec_from_file_location('_nexus_fault_baseline',file)
        baseline=importlib.util.module_from_spec(spec); sys.modules[spec.name]=baseline
        spec.loader.exec_module(baseline)
        for repeat in range(10):
            for label,cls in [('baseline',baseline.SyntheticRuntime),('fixed',SyntheticRuntime)]:
                runtime=cls(directory/f'{repeat}-{label}.db')
                runtime.submit('bad'); runtime.submit('good')
                original=runtime.execute
                def execute(payload):
                    if payload['task_id']=='bad' and payload['role']=='research':
                        raise RuntimeError('synthetic provider failure')
                    return original(payload)
                runtime.execute=execute
                started=perf_counter(); aborted=False
                try: completed=runtime.drain()
                except RuntimeError: completed=None; aborted=True
                elapsed=perf_counter()-started
                snapshot=runtime.snapshot()
                good=sum(r['status']=='completed' and r['work_id'].startswith('router:good:')
                         for r in snapshot['tasks'])
                failed=next(r for r in snapshot['tasks'] if r['work_id']=='router:bad:research')
                rows.append({'repeat':repeat,'version':label,'wall_seconds':elapsed,'aborted':aborted,
                             'reported_completed':completed,'healthy_children_completed':good,
                             'failed_item_state':failed['status'],
                             'failure_events':sum(e['kind']=='failed' for e in snapshot['events'])})
        del sys.modules[spec.name]
    assert all(r['healthy_children_completed']==0 and r['aborted'] for r in rows if r['version']=='baseline')
    assert all(r['healthy_children_completed']==3 and not r['aborted'] and r['failure_events']==1
               for r in rows if r['version']=='fixed')
    return {'schema':'nexus.failure-isolation-benchmark.v1','baseline_commit':BASELINE,
            'synthetic_faults':True,'repetitions_per_version':10,'rows':rows,
            'median_seconds':{label:statistics.median(r['wall_seconds'] for r in rows if r['version']==label)
                              for label in ['baseline','fixed']},
            'healthy_task_completion':{'baseline':'0/10','fixed':'10/10'},
            'model_calls':0,'api_cost_usd':0,'latency_note':'Fixed path completes additional work; no speedup claim.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); result=benchmark(Path(__file__).resolve().parent)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'healthy_task_completion':result['healthy_task_completion'],'median_seconds':result['median_seconds']}))
