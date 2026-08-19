from nexus_autonomy.capacity_multiplier import CapacityTask, HelperKind, plan_capacity_multiplier


def test_repeated_deterministic_task_is_delegated():
    result = plan_capacity_multiplier([CapacityTask("asset-reanalysis", 4, 10, True)])
    assert result[0].helper_kind is HelperKind.SCHEDULER
    assert result[0].estimated_minutes_saved == 40


def test_external_action_stays_human_gated():
    result = plan_capacity_multiplier([
        CapacityTask("supplier-send", 3, 5, True, consequential_external_action=True)
    ])
    assert result[0].requires_human_gate is True


def test_sensitive_task_uses_internal_worker():
    result = plan_capacity_multiplier([CapacityTask("private-analysis", 2, 15, True, sensitive=True)])
    assert result[0].helper_kind is HelperKind.WORKER


def test_invalid_or_low_value_task_is_not_delegated():
    assert plan_capacity_multiplier([CapacityTask("", 1, 1, True)]) == ()
    assert plan_capacity_multiplier([CapacityTask("one-off", 1, 30, False)]) == ()
