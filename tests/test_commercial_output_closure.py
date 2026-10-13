from commercial_output_closure import *

def test_generic_web_is_reversibly_deprecated_not_deleted():
 p={x.route:x for x in route_policies()}
 assert p["GENERIC_WEB_PROCUREMENT"].state==RouteState.DEPRECATED_PRIMARY
 assert p["GENERIC_WEB_PROCUREMENT"].replacement=="DIRECT_PROCUREMENT_AWARD"

def test_three_measured_routes_are_primary():
 p={x.route:x.state for x in route_policies()}
 assert [r for r,s in p.items() if s==RouteState.PRIMARY]==["DIRECT_PROCUREMENT_AWARD","MERCHANT_TRADE_RELATIONSHIP","OEM_INSTALLED_BASE_REVERSE"]

def test_possible_reissue_is_not_current_without_primary_binding():
 k=replay_outputs()[0]
 assert k.state==CommercialState.POSSIBLE_REISSUE
 assert not may_promote_current(k)

def test_secondary_award_does_not_become_verified_incumbent():
 a=replay_outputs()[1]
 assert a.winner=="TOO KODAVARI"
 assert not may_promote_incumbent(a)

def test_primary_bound_verified_award_can_support_incumbent_only():
 a=CommercialOutput("x","p","buyer","rollers",CommercialState.AWARD_VERIFIED,("primary",),winner="W",primary_bound=True)
 assert may_promote_incumbent(a)
 assert not may_promote_current(a)
 assert not may_execute_external(a)

def test_current_trigger_needs_primary_binding_and_deadline():
 a=CommercialOutput("x","p","buyer","chain",CommercialState.CURRENT_TRIGGER_VERIFIED,("primary",),current_deadline="2026-10-12",primary_bound=True)
 assert may_promote_current(a)
 assert not may_execute_external(a)

def test_snapshot_is_honest_about_current_state():
 s=commercial_snapshot()
 assert s=={"outputs":2,"primary_bound":0,"current_verified":0,"incumbent_verified":0,"external_actions_authorized":0}
