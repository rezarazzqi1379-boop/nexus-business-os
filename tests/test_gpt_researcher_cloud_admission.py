"""Offline safety contract for optional GPT Researcher cloud pilot.
No imports from the external package, network, cloud or API access.
Run: python -m unittest discover -s tests -p 'test_gpt_researcher_cloud_admission.py' -v
"""
import os
import re
import unittest
from dataclasses import dataclass

PINNED_UPSTREAM = "0957c301ed06c2a5857b834358c7227c739041d4"
ALLOWED_PROJECT = "PRJ-STEEL-SALES"


@dataclass(frozen=True)
class PilotAdmission:
    project_id: str
    upstream_sha: str
    synthetic_data: bool
    api_keys_present: bool
    outbound_network_enabled: bool
    external_writes_enabled: bool
    budget_usd: float
    persistent_service: bool


def admit_offline_pilot(config: PilotAdmission) -> bool:
    """Allow *only* offline, ephemeral, zero-spend synthetic tests."""
    if not isinstance(config, PilotAdmission):
        return False
    return (
        config.project_id == ALLOWED_PROJECT
        and config.upstream_sha == PINNED_UPSTREAM
        and re.fullmatch(r"[0-9a-f]{40}", config.upstream_sha) is not None
        and config.synthetic_data is True
        and config.api_keys_present is False
        and config.outbound_network_enabled is False
        and config.external_writes_enabled is False
        and type(config.budget_usd) in (int, float)
        and config.budget_usd == 0
        and config.persistent_service is False
    )


class OfflineAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.base = PilotAdmission(ALLOWED_PROJECT, PINNED_UPSTREAM, True, False, False, False, 0, False)

    def test_safe_configuration_allowed(self):
        self.assertTrue(admit_offline_pilot(self.base))

    def test_unsafe_changes_denied(self):
        from dataclasses import replace
        changes = [
            {"project_id": "PRJ-HYD-01"},
            {"upstream_sha": "main"},
            {"upstream_sha": "0" * 40},
            {"synthetic_data": False},
            {"api_keys_present": True},
            {"outbound_network_enabled": True},
            {"external_writes_enabled": True},
            {"budget_usd": 0.01},
            {"budget_usd": -1},
            {"persistent_service": True},
        ]
        for change in changes:
            with self.subTest(change=change):
                self.assertFalse(admit_offline_pilot(replace(self.base, **change)))

    def test_invalid_input_denied(self):
        self.assertFalse(admit_offline_pilot(None))
        self.assertFalse(admit_offline_pilot({"project_id": ALLOWED_PROJECT}))


if __name__ == "__main__":
    unittest.main()
