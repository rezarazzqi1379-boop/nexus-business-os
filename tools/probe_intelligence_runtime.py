"""Reproducible restart/incremental proof using synthetic claims only."""
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ['RUNTIME__DLTHUB_TELEMETRY'] = 'false'
os.environ['DLT_DATA_DIR'] = str(Path('.nexus/intelligence-runtime/dlt').resolve())
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from intelligence_dlt_adapter import load_scoped_records, verify_runtime_lock


def run():
    verify_runtime_lock(Path('config/intelligence-runtime.lock.txt'))
    rows = [dict(id='fixture-1', project_id='SANDBOX', lane='proof',
                 source_ref='fixture://rfq', origin_id='synthetic',
                 evidence_class='CLAIM', updated_at=1, buyer='fixture-buyer')]
    with TemporaryDirectory() as directory:
        root = Path(directory)
        first = load_scoped_records(rows, project_id='SANDBOX', lane='proof', root=root)
        repeat = load_scoped_records(rows, project_id='SANDBOX', lane='proof', root=root)
        changed = load_scoped_records([rows[0] | {'updated_at': 2}], project_id='SANDBOX', lane='proof', root=root)
        other = load_scoped_records([rows[0] | {'project_id': 'OTHER'}], project_id='OTHER', lane='proof', root=root)
        assert [r['emitted_rows'] for r in (first, repeat, changed, other)] == [1, 0, 1, 1], [first, repeat, changed, other]
        assert first['scope'] != other['scope']
        negatives = []
        for bad in (rows[0] | {'project_id': 'OTHER'}, rows[0] | {'source_ref': ''},
                    rows[0] | {'evidence_class': 'FACT'}):
            try:
                load_scoped_records([bad], project_id='SANDBOX', lane='proof', root=root)
            except ValueError as exc:
                negatives.append(str(exc))
        assert len(negatives) == 3
        result = dict(version='nexus.dlt-probe.v1', runs=[first, repeat, changed, other],
                      negative_checks=negatives, model_calls=0, production=False)
    target = Path('data/research/intelligence-runtime-proof.json')
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    run()
