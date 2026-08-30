import unittest

from production_probe import run_probe, validate_base_url


SECURITY_HEADERS = {
    "cache-control": "no-store",
    "content-security-policy": "default-src 'self'",
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
}


def good_transport(url: str, accept: str):
    path = "/" + url.split("/", 3)[-1]
    cases = {
        "/health": (200, {}, b'{"status":"ok"}'),
        "/ready": (200, {}, b'{"status":"ready"}'),
        "/login": (200, {}, b'<title>NEXUS</title><form action="/auth/login">'),
        "/console": (303, {"location": "/login?next=/console"}, b""),
        "/v1/system/diagnostics": (401, {}, b'{"detail":"authentication_required"}'),
    }
    status, headers, body = cases[path]
    return status, SECURITY_HEADERS | headers, body


class ProductionProbeTests(unittest.TestCase):
    def test_complete_public_boundary_passes(self):
        result = run_probe("https://nexus.example", good_transport, "2026-08-30T00:00:00+00:00")
        self.assertTrue(result["passed"])
        self.assertEqual(len(result["checks"]), 5)
        self.assertEqual(result["credential_mode"], "public-boundary-only")

    def test_missing_security_header_fails(self):
        def transport(url, accept):
            status, headers, body = good_transport(url, accept)
            headers.pop("x-frame-options")
            return status, headers, body
        result = run_probe("https://nexus.example", transport)
        self.assertFalse(result["passed"])
        self.assertTrue(all("x-frame-options" in item["missing_security_headers"] for item in result["checks"]))

    def test_wrong_redirect_fails(self):
        def transport(url, accept):
            status, headers, body = good_transport(url, accept)
            if url.endswith("/console"):
                headers["location"] = "/unexpected"
            return status, headers, body
        result = run_probe("https://nexus.example", transport)
        self.assertFalse(next(item for item in result["checks"] if item["name"] == "console_redirect")["passed"])

    def test_private_and_credential_urls_are_rejected(self):
        for value in ("http://example.com", "https://localhost", "https://127.0.0.1", "https://user:pass@example.com"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_base_url(value)

    def test_query_and_fragment_are_rejected(self):
        for value in ("https://example.com/?token=x", "https://example.com/#secret"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_base_url(value)


if __name__ == "__main__":
    unittest.main()
