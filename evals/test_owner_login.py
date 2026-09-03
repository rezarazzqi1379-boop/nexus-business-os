from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from security import (
    issue_session,
    legacy_owner_login,
    login_config_valid,
    login_password_authorized,
    session_authorized,
)


class OwnerLoginSeparationTests(unittest.TestCase):
    def env(self, **values):
        base = {
            "NEXUS_AUTH_REQUIRED": "1",
            "NEXUS_ACCESS_TOKEN": "a" * 40,
            "NEXUS_OWNER_PASSWORD": "",
            "NEXUS_SESSION_SECRET": "",
            "NEXUS_SESSION_TTL_SECONDS": "3600",
        }
        base.update(values)
        return patch.dict(os.environ, base, clear=True)

    def test_legacy_fallback_preserves_existing_login(self):
        with self.env():
            self.assertTrue(legacy_owner_login())
            self.assertTrue(login_password_authorized("a" * 40))

    def test_owner_password_is_independent_from_api_token(self):
        with self.env(NEXUS_OWNER_PASSWORD="owner-password-strong-123"):
            self.assertFalse(legacy_owner_login())
            self.assertTrue(login_password_authorized("owner-password-strong-123"))
            self.assertFalse(login_password_authorized("a" * 40))

    def test_short_owner_password_fails_closed(self):
        with self.env(NEXUS_OWNER_PASSWORD="too-short"):
            self.assertFalse(login_config_valid())
            self.assertFalse(login_password_authorized("too-short"))

    def test_owner_password_rotation_revokes_existing_session(self):
        with self.env(NEXUS_OWNER_PASSWORD="owner-password-strong-123"):
            cookie = issue_session(now=1_000)
            self.assertTrue(session_authorized(cookie, now=1_001))
        with self.env(NEXUS_OWNER_PASSWORD="owner-password-rotated-456"):
            self.assertFalse(session_authorized(cookie, now=1_001))

    def test_session_secret_rotation_revokes_existing_session(self):
        with self.env(
            NEXUS_OWNER_PASSWORD="owner-password-strong-123",
            NEXUS_SESSION_SECRET="s" * 40,
        ):
            cookie = issue_session(now=1_000)
            self.assertTrue(session_authorized(cookie, now=1_001))
        with self.env(
            NEXUS_OWNER_PASSWORD="owner-password-strong-123",
            NEXUS_SESSION_SECRET="t" * 40,
        ):
            self.assertFalse(session_authorized(cookie, now=1_001))


if __name__ == "__main__":
    unittest.main()
