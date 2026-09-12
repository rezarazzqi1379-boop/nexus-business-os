from dataclasses import replace
from pathlib import Path

import pytest

from self_improvement_runtime import SystemExercise, record_cycle, run_self_improvement_cycle
from unified_data_environment import UnifiedDataHub


def exercise(number: int, **changes) -> SystemExercise:
    item = SystemExercise(f"exercise-{number}", "conversation-control", "NEXUS_CORE",
                          f"task-{number}", "bounded-context", (f"pytest:run-{number}",),
                          ("normalize", "allocate"), (f"pytest lane-{number}",),
                          ("constraints preserved", "token budget bounded"), "SUCCESS", 0,
                          ("load summaries before raw histories",), "2026-09-12T10:00:00+00:00")
    return replace(item, **changes)


def test_three_clean_exercises_create_experiment_only():
    report = run_self_improvement_cycle(tuple(exercise(n) for n in range(3)),
                                        project_id="NEXUS_CORE", rollback_ref="git:working-tree")
    assert report.candidates[0].decision == "EXPERIMENT"
    assert report.production_changes_applied is False


def test_insufficient_or_corrected_evidence_cannot_propose():
    report = run_self_improvement_cycle((exercise(1), exercise(2, human_corrections=1)),
                                        project_id="NEXUS_CORE", rollback_ref="git:working-tree")
    assert report.candidates == ()
    assert report.ineligible_exercises == ("exercise-2",)


def test_identity_collision_and_cross_project_fail_closed():
    with pytest.raises(ValueError, match="collision"):
        run_self_improvement_cycle((exercise(1), exercise(1, task_id="different")),
                                   project_id="NEXUS_CORE", rollback_ref="rollback")
    with pytest.raises(ValueError, match="cross_project"):
        run_self_improvement_cycle((exercise(1, project_id="OTHER"),),
                                   project_id="NEXUS_CORE", rollback_ref="rollback")


def test_report_is_recorded_in_unified_hub(tmp_path: Path):
    report = run_self_improvement_cycle(tuple(exercise(n) for n in range(3)),
                                        project_id="NEXUS_CORE", rollback_ref="rollback")
    hub = UnifiedDataHub(tmp_path / "hub.db", tmp_path)
    assert record_cycle(hub, report, "2026-09-12T11:00:00+00:00")
    assert record_cycle(hub, report, "2026-09-12T11:00:00+00:00") is False
    assert hub.project_view("NEXUS_CORE")[0]["category"] == "SELF_IMPROVEMENT_EXPERIMENT"
