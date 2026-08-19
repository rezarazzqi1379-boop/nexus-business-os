from nexus_core.plugin_expertise import PluginExpertise, WorkLane, assign_parallel_lanes


def test_assigns_verified_specialists_and_preserves_human_gate():
    plugins = [
        PluginExpertise("Consensus", "science", ("literature",), "read_verified"),
        PluginExpertise("GitHub", "code", ("repository", "ci"), "write_verified"),
        PluginExpertise("HubSpot", "crm", ("deals",), "write_verified"),
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
    plugins = [PluginExpertise("GitHub", "code", ("code",), "write_verified")]
    lanes = [WorkLane(f"lane-{i}", "code", 100 - i, 50) for i in range(8)]
    assert len(assign_parallel_lanes(plugins, lanes, max_parallel=4)) == 4
