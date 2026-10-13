from adapter_router import *
def test_unknown_tooling_does_not_expand_architecture():
 assert route("make_everything_autonomous")=="NO_ADAPTER_JUSTIFIED"
def test_paid_apollo_never_auto_runs():
 assert not can_auto_use("APOLLO",paid=True)
def test_external_writes_remain_gated():
 assert not can_auto_use("HUBSPOT",external_write=True)
def test_read_discovery_adapter_can_route():
 assert route("trade_discovery")=="ABRAMS"
