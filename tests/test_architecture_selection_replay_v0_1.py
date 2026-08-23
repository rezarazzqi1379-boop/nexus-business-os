import json
from pathlib import Path

from nexus_control_plane.architecture_selector import (
    ArchitectureSelectionInput,
    select_agent_architecture,
)


def test_representative_nexus_work_selects_expected_architecture():
    path = Path(__file__).parents[1] / "data" / "architecture_selection_replay_v0_1.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["version"] == "0.1"
    assert len(data["cases"]) >= 5

    for case in data["cases"]:
        inp = ArchitectureSelectionInput(
            parallelizable_fraction=case["parallelizable_fraction"],
            sequential_dependency=case["sequential_dependency"],
            tool_count=case["tool_count"],
            context_degradation=case["context_degradation"],
            independent_verification_available=case["independent_verification_available"],
            latency_priority=case.get("latency_priority", 0.5),
            cost_priority=case.get("cost_priority", 0.5),
        )
        out = select_agent_architecture(inp)
        assert out.architecture.value == case["expected_architecture"], case["id"]
