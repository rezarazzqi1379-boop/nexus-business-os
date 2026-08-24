import json
import unittest
from pathlib import Path

from commercial_entry import load_entry_packets


DATA = Path(__file__).parents[1] / "data" / "commercial_entry_packets_2026-08-21.json"


class CommercialEntryTests(unittest.TestCase):
    def test_packets_are_sorted_by_priority(self):
        packets = load_entry_packets(DATA)
        self.assertEqual([packet.priority for packet in packets], [1, 2, 3, 4])

    def test_prepared_packets_cannot_be_sent(self):
        packets = load_entry_packets(DATA)
        self.assertTrue(all(not packet.ready_to_send(human_approved=True) for packet in packets))

    def test_global_send_authorization_is_false(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        self.assertFalse(payload["send_authorized"])

    def test_every_packet_has_stop_conditions(self):
        packets = load_entry_packets(DATA)
        self.assertTrue(all(packet.stop_conditions for packet in packets))


if __name__ == "__main__":
    unittest.main()
