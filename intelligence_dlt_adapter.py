"""Optional dlt incremental adapter; local sandbox destination only."""
from hashlib import sha256
from pathlib import Path
from typing import Iterable


def verify_runtime_lock(lock: Path):
    from importlib.metadata import version
    checked = 0
    for line in lock.read_text(encoding='utf-8').splitlines():
        if not line.strip() or line.startswith('#'):
            continue
        package, expected = line.split(' --hash=', 1)[0].split('==', 1)
        if version(package) != expected:
            raise ValueError('runtime_version_drift:' + package)
        checked += 1
    if checked == 0:
        raise ValueError('empty_runtime_lock')
    return checked


def load_scoped_records(records: Iterable[dict], *, project_id: str, lane: str, root: Path):
    if not project_id.strip() or not lane.strip():
        raise ValueError('scope_required')
    rows = list(records)
    # Validate the whole batch before creating state or advancing its cursor.
    for row in rows:
        if (row.get('project_id'), row.get('lane')) != (project_id, lane):
            raise ValueError('cross_scope_blocked')
        if any(not isinstance(row.get(k), str) or not row[k].strip()
               for k in ('id', 'source_ref', 'origin_id', 'evidence_class')):
            raise ValueError('lineage_required')
        if row['evidence_class'] != 'CLAIM':
            raise ValueError('automatic_promotion_blocked')
        if type(row.get('updated_at')) is not int or row['updated_at'] < 0:
            raise ValueError('invalid_cursor')
    import dlt
    from dlt.destinations import filesystem
    scope = sha256(f'{project_id}\0{lane}'.encode()).hexdigest()[:24]
    root = root.resolve()
    resource = dlt.resource(rows, name='evidence', primary_key='id',
                            write_disposition='append')
    resource.apply_hints(incremental=dlt.sources.incremental('updated_at', initial_value=0))
    pipeline = dlt.pipeline(pipeline_name=f'nexus_{scope}',
                            pipelines_dir=str(root / 'pipelines'),
                            destination=filesystem(bucket_url=(root / 'data').as_uri()),
                            dataset_name=f'claims_{scope}')
    pipeline.run(resource, loader_file_format='jsonl')
    normalization = pipeline.last_trace.last_normalize_info
    emitted = normalization.row_counts.get('evidence', 0) if normalization else 0
    return {'scope': scope, 'input_rows': len(rows),
            'emitted_rows': emitted, 'maturity': 'SANDBOX', 'dlt_version': dlt.__version__}
