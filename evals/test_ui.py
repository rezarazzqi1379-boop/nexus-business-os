from __future__ import annotations

import unittest
from html.parser import HTMLParser
from pathlib import Path

from console_contract import APP_VERSION, build_console_bootstrap


ROOT = Path(__file__).parents[1]


class ComponentCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.components: set[str] = set()
        self.nexus_components: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("data-component"):
            self.components.add(str(values["data-component"]))
        if values.get("data-nexus-component"):
            self.nexus_components.add(str(values["data-nexus-component"]))


class OperatorConsoleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = (ROOT / "ui" / "index.html").read_text(encoding="utf-8")
        self.css = (ROOT / "ui" / "styles.css").read_text(encoding="utf-8")
        self.js = (ROOT / "ui" / "app.js").read_text(encoding="utf-8")
        self.parser = ComponentCollector()
        self.parser.feed(self.html)

    def test_all_twenty_agent_ui_patterns_exist(self):
        expected = {
            "loading-state", "thinking", "streaming-text", "approval-card", "tool-chips",
            "task-rows", "chat", "prompt-bar", "recommendation-card", "context-cards",
            "diff-table", "records-table", "filter-table", "sidebar-nav", "search",
            "flowchart", "insight-cards", "code-block", "fine-tune-card", "selection-actions",
        }
        self.assertEqual(self.parser.components, expected)

    def test_nexus_specific_control_components_exist(self):
        self.assertEqual(self.parser.nexus_components, {
            "approval-fingerprint", "evidence-ledger", "connector-health",
            "constraint-guard", "cost-meter", "recovery-checkpoint",
        })

    def test_console_bootstrap_is_explicitly_read_only(self):
        payload = build_console_bootstrap()
        self.assertEqual(payload["mode"], "read_only_pilot")
        self.assertIs(payload["external_writes_enabled"], False)
        self.assertTrue(any(item["state"] == "auth_broken" for item in payload["connectors"]))

    def test_health_reports_ui_release(self):
        self.assertEqual(APP_VERSION, "1.9.0")

    def test_mobile_and_reduced_motion_rules_exist(self):
        self.assertIn("@media(max-width:720px)", self.css)
        self.assertIn("@media(prefers-reduced-motion:reduce)", self.css)
        self.assertNotIn("user-scalable=no", self.html)

    def test_approval_preview_cannot_call_external_write(self):
        self.assertIn("هیچ ایمیلی ارسال نمی‌کند", self.html)
        self.assertNotIn("/v1/approvals/decide", self.js)
        self.assertNotIn("send_email(", self.js)

    def test_dynamic_content_is_html_escaped(self):
        self.assertIn("function escapeHtml", self.js)
        self.assertIn("escapeHtml(project.name)", self.js)
        self.assertIn("escapeHtml(value)", self.js)

    def test_accessibility_landmarks_and_live_regions_exist(self):
        for token in ('id="main"', 'aria-label="ناوبری اصلی"', 'aria-live="polite"', 'role="status"'):
            self.assertIn(token, self.html)


if __name__ == "__main__":
    unittest.main()
