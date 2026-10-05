from held_out_red_team_runner import run_existing_controls

def test_existing_controls_defeat_supported_held_out_attacks():
 r=run_existing_controls()
 assert not r["failed"]
 for fid in ("rt-source-001","rt-time-001","rt-trade-001","rt-coverage-001","rt-provider-001"):
  assert fid in r["passed"]

def test_unimplemented_attack_families_stay_not_run():
 r=run_existing_controls()
 for fid in ("rt-role-001","rt-price-001","rt-eq-001","rt-entity-001"):
  assert fid in r["not_run"]
 assert not r["complete"]
