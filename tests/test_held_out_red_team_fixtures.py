import pytest
from held_out_red_team_fixtures import HELD_OUT,evaluate_outcomes,registry

def test_registry_has_independent_attack_families():
 xs=registry()
 assert len(xs)==9 and len({x.fixture_id for x in xs})==len(xs)

def test_fixture_cannot_pass_without_evidence():
 f=HELD_OUT[0]
 r=evaluate_outcomes({f.fixture_id:(f.expected,())})
 assert f.fixture_id in r["failed"] and not r["complete"]

def test_unexecuted_fixtures_remain_visible():
 r=evaluate_outcomes({})
 assert len(r["not_run"])==len(HELD_OUT) and not r["complete"]

def test_wrong_observation_fails_even_with_evidence():
 f=HELD_OUT[0]
 r=evaluate_outcomes({f.fixture_id:("manufacturer",("test:1",))})
 assert f.fixture_id in r["failed"]

def test_complete_only_when_every_fixture_matches_with_evidence():
 outcomes={f.fixture_id:(f.expected,(f"test:{f.fixture_id}",)) for f in HELD_OUT}
 r=evaluate_outcomes(outcomes)
 assert r["complete"] and not r["failed"] and not r["not_run"]
