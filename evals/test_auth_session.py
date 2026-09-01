import base64
import os
import unittest

import security


class AuthUpgradeTests(unittest.TestCase):
    def setUp(self):
        os.environ["NEXUS_ACCESS_TOKEN"] = "a" * 64
        os.environ["NEXUS_AUTH_REQUIRED"] = "1"
        os.environ["NEXUS_SESSION_TTL_SECONDS"] = "3600"

    def tearDown(self):
        for key in ("NEXUS_ACCESS_TOKEN", "NEXUS_AUTH_REQUIRED", "NEXUS_SESSION_TTL_SECONDS", "NEXUS_BASIC_CHALLENGE"):
            os.environ.pop(key, None)

    def test_basic_auth_uses_password_component(self):
        header = "Basic " + base64.b64encode(("reza:" + "a" * 64).encode()).decode()
        self.assertTrue(security._authorized(header))

    def test_basic_challenge_disabled_by_default(self):
        self.assertFalse(security.basic_challenge_enabled())

    def test_basic_challenge_can_be_explicitly_enabled(self):
        os.environ["NEXUS_BASIC_CHALLENGE"] = "1"
        self.assertTrue(security.basic_challenge_enabled())

    def test_signed_session_round_trip(self):
        cookie = security.issue_session(now=1000)
        self.assertTrue(security.session_authorized(cookie, now=1001))

    def test_expired_session_is_rejected(self):
        cookie = security.issue_session(now=1000)
        self.assertFalse(security.session_authorized(cookie, now=5000))

    def test_tampered_session_is_rejected(self):
        cookie = security.issue_session(now=1000)
        self.assertFalse(security.session_authorized(cookie[:-1] + "0", now=1001))

    def test_token_rotation_revokes_session(self):
        cookie = security.issue_session(now=1000)
        os.environ["NEXUS_ACCESS_TOKEN"] = "b" * 64
        self.assertFalse(security.session_authorized(cookie, now=1001))

    def test_invalid_ttl_falls_back(self):
        os.environ["NEXUS_SESSION_TTL_SECONDS"] = "invalid"
        self.assertEqual(security.session_ttl_seconds(), security.DEFAULT_SESSION_TTL_SECONDS)


if __name__ == "__main__":
    unittest.main()
