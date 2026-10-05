import pytest
from relationship_benchmark import *

def test_relationship_metrics():
 r=metrics(RelationshipBenchmark(4,1,2,5,3,2))
 assert r["verified_relationship_yield"]==.25 and r["false_edge_prevention_rate"]==.5

def test_comparison_refuses_rate_delta_on_different_relationship_budget():
 r=compare(RelationshipBenchmark(2,0,1,2,1,0),RelationshipBenchmark(4,1,2,5,3,2))
 assert not r["comparable_relationship_budget"] and r["verified_relationship_yield_delta"] is None

def test_invalid_counts_fail_closed():
 with pytest.raises(ValueError):metrics(RelationshipBenchmark(1,2,0,0,0,0))
