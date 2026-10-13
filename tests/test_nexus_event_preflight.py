import unittest
from dataclasses import dataclass

from nexus_event_preflight import preflight_event


NOW = "2026-09-11T12:00:00+00:00"


@dataclass
class Event:
    event_id: str
    project: str
    payload: dict


def authority(evidence_id, key):
    return {
        "evidence_id": evidence_id,
        "connector_id": "github",
        "project_id": "PRJ-HYD-01",
        "semantic_key": key,
        "value": "current",
        "classification": "FACT",
        "source_locator": f"github://{evidence_id}",
        "observed_at": NOW,
    }


class EventPreflightTests(unittest.TestCase):
    def test_missing_context_blocks_before_model_entry(self):
        result = preflight_event(Event("evt-1", "PRJ-HYD-01", {}))
        self.assertEqual(result["gate"], "BLOCK")
        self.assertEqual(result["findings"][0]["code"], "PREFLIGHT_CONTEXT_MISSING")

    def test_complete_event_context_passes(self):
        payload = {"_nexus_preflight": {
            "now": NOW,
            "required_connectors": ["github"],
            "snapshots": [{
                "connector_id": "github", "observed_at": NOW,
                "state": "AVAILABLE", "source_revision": "commit-1",
            }],
            "evidence": [
                authority("registry", "authority.source_registry"),
                authority("master", "authority.project_master"),
            ],
        }}
        result = preflight_event(Event("evt-1", "PRJ-HYD-01", payload))
        self.assertEqual(result["gate"], "SAFE")

    def acquisition_payload(self, **changes):
        acquisition = dict(lane_id="discovery", needs_external_evidence=True,
                           sensitivity="public", native_available=False,
                           cache_fresh=False, reach_healthy=True,
                           health_age_seconds=5, remaining_queries=2,
                           health_evidence_ref="evidence://live-read-1",
                           health_measurement_kind="live_read")
        acquisition.update(changes)
        return {"_nexus_preflight": {
            "now": NOW, "acquisition": acquisition,
            "required_connectors": ["github"],
            "snapshots": [{"connector_id": "github", "observed_at": NOW,
                           "state": "AVAILABLE", "source_revision": "commit-1"}],
            "evidence": [authority("registry", "authority.source_registry"),
                         authority("master", "authority.project_master")],
        }}

    def test_acquisition_is_in_actual_event_preflight(self):
        result = preflight_event(Event("evt", "PRJ-HYD-01", self.acquisition_payload()))
        self.assertEqual(result["gate"], "SAFE")
        self.assertEqual(result["acquisition"]["route"], "agent_reach")

    def test_installed_only_health_is_not_live_health(self):
        result = preflight_event(Event("evt", "PRJ-HYD-01",
            self.acquisition_payload(health_measurement_kind="doctor")))
        self.assertEqual(result["gate"], "BLOCK")
        self.assertEqual(result["acquisition"]["reason"], "live_read_health_proof_required")

    def test_stale_channel_blocks_before_model(self):
        result = preflight_event(Event("evt", "PRJ-HYD-01",
            self.acquisition_payload(health_age_seconds=3601)))
        self.assertEqual(result["gate"], "BLOCK")

    def test_project_mismatch_blocks(self):
        result = preflight_event(Event("evt", "PRJ-HYD-01",
            self.acquisition_payload(project_id="PRJ-KCL-01")))
        self.assertEqual(result["gate"], "BLOCK")

    def test_native_route_needs_no_reach_probe(self):
        result = preflight_event(Event("evt", "PRJ-HYD-01",
            self.acquisition_payload(native_available=True, reach_healthy=False)))
        self.assertEqual(result["gate"], "SAFE")
        self.assertEqual(result["acquisition"]["route"], "native")

    def test_malformed_context_fails_closed(self):
        payload = {"_nexus_preflight": {"snapshots": [{"connector_id": "github"}]}}
        result = preflight_event(Event("evt-1", "PRJ-HYD-01", payload))
        self.assertEqual(result["gate"], "BLOCK")
        self.assertEqual(result["findings"][0]["code"], "PREFLIGHT_CONTEXT_INVALID")

    def test_agent_source_invokes_preflight_before_model(self):
        source = (CONFIG_PATH / "agent.py").read_text(encoding="utf-8")
        self.assertLess(source.index("preflight = preflight_event(event)"), source.index("ResponsesClient().run"))


CONFIG_PATH = __import__("pathlib").Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    unittest.main()
