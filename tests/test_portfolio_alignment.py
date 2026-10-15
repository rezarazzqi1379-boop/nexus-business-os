from nexus_core.portfolio_alignment import gate_work, get_project_control


def test_hydrotester_duplicate_follow_up_is_blocked_but_internal_work_allowed():
    assert gate_work("PRJ-HYD-01", consequential=False) == "ALLOW_INTERNAL"
    assert gate_work("PRJ-HYD-01", consequential=False, is_follow_up=True) == "BLOCK_DUPLICATE_OUTREACH"


def test_heat_treatment_remains_on_management_hold():
    assert gate_work("PRJ-HTL-01", consequential=False) == "HOLD"
    assert gate_work("PRJ-HTL-01", consequential=True) == "HOLD"


def test_kcl_requires_refresh_before_consequential_use():
    control = get_project_control("PRJ-KCL-01")
    assert "quantity_forecast" in control.dynamic_unknowns
    assert "sanctions_logistics_feasibility" in control.dynamic_unknowns
    assert gate_work("PRJ-KCL-01", consequential=False) == "ALLOW_INTERNAL"
    assert gate_work("PRJ-KCL-01", consequential=True) == "REFRESH_FIRST"


def test_can_forming_requires_engineering_refresh_before_consequential_use():
    control = get_project_control("PRJ-CAN-01")
    assert set(control.dynamic_unknowns) == {"final_geometry", "mandatory_operations", "production_rate"}
    assert gate_work("PRJ-CAN-01", consequential=True) == "REFRESH_FIRST"


def test_unknown_project_fails_closed():
    try:
        gate_work("PRJ-UNKNOWN", consequential=False)
    except ValueError as exc:
        assert "unknown or duplicate project control" in str(exc)
    else:
        raise AssertionError("unknown project must fail closed")
