from pathlib import Path

from nexus_system_bootstrap import activate
from unified_data_environment import BackupManager


def test_activation_creates_hub_watchdog_and_verified_snapshot(tmp_path: Path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "sample.json").write_text("{}", encoding="utf-8")
    status = activate(tmp_path, snapshot_id="test-snapshot")
    assert status["snapshot_verified"] is True
    assert status["portfolio_coverage"] == status["portfolio_projects"]
    assert (tmp_path / status["hub"]).is_file()
    assert BackupManager.verify_snapshot(tmp_path / status["snapshot"])
