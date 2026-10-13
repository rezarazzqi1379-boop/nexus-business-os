from outcome_census import *

def test_registered_search_counts_match_two_three_search_cycles():
 assert all(x.searches==6 for x in registered_benchmarks())

def test_merchant_hub_has_measured_relationship_yield():
 m=registered_benchmarks()[0]
 assert m.relationship_bound==2
 assert conversion_yield(m)>0
 assert decision(m)=="KEEP_AND_BIND_NEXT_EDGE"

def test_application_first_is_support_not_conversion_winner():
 a=registered_benchmarks()[1]
 assert a.relationship_bound==0 and a.current_trigger==0
 assert decision(a)=="SUPPORT_OR_REROUTE"

def test_generic_web_procurement_is_rerouted_not_called_no_demand():
 p=registered_benchmarks()[2]
 assert conversion_yield(p)==0
 assert decision(p)=="SUPPORT_OR_REROUTE"
 assert "DIRECT_PROCUREMENT_AWARD" in priority_routes()

def test_guard_value_is_measured_separately_from_conversion():
 for x in registered_benchmarks():
  assert guard_yield(x)==1.0

def test_activity_without_outcome_is_stopped_or_redesigned():
 x=RouteOutcome("BUSY_AGENT",100)
 assert decision(x)=="STOP_OR_REDESIGN"
 assert conversion_yield(x)==0
