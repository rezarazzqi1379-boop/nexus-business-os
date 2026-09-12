from portfolio_watchdog import ProjectPulse, watch_portfolio
from projects import PROJECTS


def test_every_project_is_covered_and_neglected_projects_get_recovery_lane():
    pulses = (ProjectPulse("hydrostatic_tester", 1000, 990, 1, 4, 1),)
    result = watch_portfolio(PROJECTS.values(), pulses, now=1000, neglect_after=100)
    assert len(result.coverage) == len(PROJECTS)
    assert "kcl_mop" in result.neglected_projects
    assert "watch-hydrostatic_tester" in result.coverage


def test_hold_project_is_visible_but_waiting_when_fresh():
    pulses = tuple(ProjectPulse(pid, 1000, 990, 0, 2, 1) for pid in PROJECTS)
    result = watch_portfolio(PROJECTS.values(), pulses, now=1000)
    assert "watch-heat_treatment" in result.schedule.waiting

