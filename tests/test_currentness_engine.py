from currentness_engine import *
def test_profile_update_does_not_refresh_old_shipment():
 assert classify_currentness("2023-06-08","2026-10-07")=="STALE"
 assert profile_update_can_refresh_observation("2023-06-08","2026-09-25") is False
def test_recent_observation():
 assert classify_currentness("2026-08-29","2026-10-07")=="CURRENT"
