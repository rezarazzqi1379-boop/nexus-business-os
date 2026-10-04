import os
import unittest
from unittest.mock import patch

from posthog_adapter import PostHogAdapter, PostHogConfig


class _Response:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class PostHogAdapterTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.dict(os.environ, {}, clear=True):
            config = PostHogConfig.from_env()
        self.assertFalse(config.enabled)
        self.assertFalse(PostHogAdapter(config).capture("nexus.test", "local")["sent"])

    def test_enabled_requires_explicit_host_and_key(self):
        with patch.dict(os.environ, {"NEXUS_POSTHOG_ENABLED": "1"}, clear=True):
            with self.assertRaises(ValueError):
                PostHogConfig.from_env()

    @patch("posthog_adapter.request.urlopen", return_value=_Response())
    def test_capture_sends_when_enabled(self, urlopen):
        config = PostHogConfig("phc_test", "https://example.invalid", True)
        result = PostHogAdapter(config).capture("nexus.test", "local", {"project_id": "PRJ-NXO-01"})
        self.assertTrue(result["sent"])
        self.assertEqual(result["status"], 200)
        self.assertEqual(urlopen.call_count, 1)

    @patch("posthog_adapter.request.urlopen", side_effect=TimeoutError())
    def test_capture_failure_does_not_raise(self, _urlopen):
        config = PostHogConfig("phc_test", "https://example.invalid", True)
        result = PostHogAdapter(config).capture("nexus.test", "local")
        self.assertFalse(result["sent"])
        self.assertEqual(result["reason"], "TimeoutError")


if __name__ == "__main__":
    unittest.main()
