from pathlib import Path
import pytest
from intelligence_dlt_adapter import load_scoped_records, verify_runtime_lock


@pytest.mark.parametrize('row', [
    {'project_id': 'OTHER', 'lane': 'proof'},
    {'project_id': 'SANDBOX', 'lane': 'other'},
    {'project_id': 'SANDBOX', 'lane': 'proof'},
    {'project_id': 'SANDBOX', 'lane': 'proof', 'id': '1', 'source_ref': 'u',
     'origin_id': 'o', 'evidence_class': 'FACT', 'updated_at': 1},
    {'project_id': 'SANDBOX', 'lane': 'proof', 'id': '1', 'source_ref': 'u',
     'origin_id': 'o', 'evidence_class': 'CLAIM', 'updated_at': True},
])
def test_bad_batch_rejected_before_runtime_state(tmp_path, row):
    target = tmp_path / 'state'
    with pytest.raises(ValueError):
        load_scoped_records([row], project_id='SANDBOX', lane='proof', root=target)
    assert not target.exists()


def test_runtime_version_drift_fails_closed(tmp_path, monkeypatch):
    import importlib.metadata
    lock = tmp_path / 'lock.txt'
    lock.write_text('dlt==1.31.0 --hash=sha256:fixture\n', encoding='utf-8')
    monkeypatch.setattr(importlib.metadata, 'version', lambda name: 'other')
    with pytest.raises(ValueError, match='runtime_version_drift'):
        verify_runtime_lock(lock)


def test_empty_runtime_lock_rejected(tmp_path):
    lock = tmp_path / 'lock.txt'
    lock.write_text('', encoding='utf-8')
    with pytest.raises(ValueError, match='empty_runtime_lock'):
        verify_runtime_lock(lock)
