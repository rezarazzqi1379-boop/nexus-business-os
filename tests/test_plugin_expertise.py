import pytest

from nexus_core.plugin_expertise import PluginExpertise, WorkLane, assign_parallel_lanes


def test_assigns_verified_specialists_and_preserves_human_gate():
    plugins = [
        PluginExpertise("Consensus", "science", ("literature",), "read_verified", evidence_ref="probe:consensus:2026-08-20"),
        PluginExpertise("GitHub", "code", ("repository", "ci"), "write_verified", evidence_ref="probe:github:2026-08-20"),
        PluginExpertise("HubSpot", "crm", ("deals",), "write_verified", evidence_ref="probe:hubspot:2026-08-20"),
    ]
    lanes = [
        WorkLane("deep-research", "science", 80, 60),
        WorkLane("runtime-code", "code", 95, 90),
        WorkLane("customer-write", "crm", 90, 80, external_effect=True),
    ]
    result = assign_parallel_lanes(plugins, lanes, max_parallel=3)
    by_lane = {item.lane: item for item in result}
    assert by_lane["runtime-code"].plugin == "GitHub"
    assert by_lane["deep-research"].plugin == "Consensus"
    assert by_lane["customer-write"].plugin == "HubSpot"
    assert by_lane["customer-write"].human_gate is True


def test_unverified_plugin_is_not_used():
    plugins = [PluginExpertise("X", "science", ("research",), "authenticated")]
    lanes = [WorkLane("research", "science", 50, 50)]
    result = assign_parallel_lanes(plugins, lanes)
    assert result[0].plugin is None
    assert result[0].reason == "no_verified_specialist"


def test_parallelism_is_bounded():
    plugins = [PluginExpertise("GitHub", "code", ("code",), "write_verified", evidence_ref="probe:github:2026-08-20")]
    lanes = [WorkLane(f"lane-{i}", "code", 100 - i, 50) for i in range(8)]
    assert len(assign_parallel_lanes(plugins, lanes, max_parallel=4)) == 4


def test_verified_plugin_requires_retrievable_evidence_reference():
    plugins = [PluginExpertise("Ghost", "science", ("research",), "read_verified")]
    with pytest.raises(ValueError, match="verified_plugin_requires_evidence_ref"):
        assign_parallel_lanes(plugins, [WorkLane("research", "science", 50, 50)])


def test_truthy_non_boolean_external_effect_fails_closed():
    plugins = [PluginExpertise("GitHub", "code", ("code",), "read_verified", evidence_ref="probe:github:2026-08-20")]
    bad_lane = WorkLane("runtime-code", "code", 80, 80, external_effect=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid_external_effect"):
        assign_parallel_lanes(plugins, [bad_lane])


def test_boolean_score_is_not_treated_as_integer_priority():
    plugins = [PluginExpertise("GitHub", "code", ("code",), "read_verified", evidence_ref="probe:github:2026-08-20")]
    bad_lane = WorkLane("runtime-code", "code", True, 80)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="score_out_of_range"):
        assign_parallel_lanes(plugins, [bad_lane])
