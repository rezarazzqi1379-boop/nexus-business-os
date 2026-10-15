import json
from pathlib import Path


def load_fixture():
    return json.loads(Path("data/project_fabric_shadow_v0_1.json").read_text())


def test_shadow_fixture_is_not_misrepresented_as_live_state():
    data = load_fixture()
    assert data["status"] == "shadow_fixture_not_live_state"


def test_shadow_fixture_has_unique_projects_and_metrics():
    data = load_fixture()
    ids = [item["project_id"] for item in data["projects"]]
    assert len(ids) == len(set(ids))
    assert all(item["target_metrics"] for item in data["projects"])


def test_waiting_can_forming_remains_no_duplicate_action():
    data = load_fixture()
    can = next(item for item in data["projects"] if item["project_id"] == "can-forming")
    assert can["state"] == "waiting"
    assert can["coordination_action"] == "watch_no_duplicate_action"


def test_hydrotester_replay_is_authority_first():
    data = load_fixture()
    hydro = next(item for item in data["projects"] if item["project_id"] == "hydrotester")
    assert hydro["coordination_action"] == "authority_first"
