from nexus_autonomy.capability_exploration import (
    CapabilityExperiment, ExplorationDecision, evaluate_capability,
)


def test_new_reversible_capability_goes_to_pilot():
    e = CapabilityExperiment("tool-x", "new research angle", True, True, False, False)
    assert evaluate_capability(e) is ExplorationDecision.PILOT


def test_positive_measured_non_sensitive_capability_can_promote():
    e = CapabilityExperiment("tool-x", "new research angle", True, True, False, False, 0.25)
    assert evaluate_capability(e) is ExplorationDecision.PROMOTE


def test_permission_broadening_never_auto_promotes():
    e = CapabilityExperiment("tool-x", "automation", True, True, False, True, 1.0)
    assert evaluate_capability(e) is ExplorationDecision.EXPLORE


def test_sensitive_capability_does_not_auto_promote():
    e = CapabilityExperiment("tool-x", "analysis", True, True, True, False, 1.0)
    assert evaluate_capability(e) is ExplorationDecision.REJECT
