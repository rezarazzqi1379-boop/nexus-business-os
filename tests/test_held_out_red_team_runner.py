from held_out_red_team_runner import run_existing_controls

def test_existing_controls_defeat_supported_held_out_attacks():
 r=run_existing_controls()
 assert not r["failed"]
 for fid in ("rt-source-001","rt-time-001","rt-trade-001","rt-coverage-001","rt-provider-001"):
  assert fid in r["passed"]

def test_all_registered_held_out_attacks_are_executed():
 r=run_existing_controls()
 assert r["complete"]
 assert not r["failed"] and not r["not_run"]
