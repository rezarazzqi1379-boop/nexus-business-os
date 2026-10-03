import math
import unittest
from source_failover import agent_reach_preflight


def run(**changes):
    args = dict(project_id="PRJ-HYD-01", lane_id="discovery",
                needs_external_evidence=True, sensitivity="public",
                native_available=False, cache_fresh=False, reach_healthy=True,
                health_age_seconds=10, remaining_queries=2)
    args.update(changes)
    return agent_reach_preflight(**args)


ROUTES = [
    ({}, "agent_reach"),
    ({"needs_external_evidence": False}, "skip"),
    ({"native_available": True}, "native"),
    ({"cache_fresh": True, "native_available": True}, "cache"),
    ({"sensitivity": "confidential", "cache_fresh": True}, "native_only"),
    ({"reach_healthy": False}, "blocked"),
    ({"health_age_seconds": 3601}, "blocked"),
    ({"remaining_queries": 0}, "blocked"),
]

def check_routing(changes, route):
    decision = run(**changes)
    assert decision.route == route
    assert decision.project_id == "PRJ-HYD-01"
    assert decision.lane_id == "discovery"


INVALID = [
    {"project_id": ""}, {"lane_id": " "}, {"sensitivity": "unknown"},
    {"health_age_seconds": math.nan}, {"health_age_seconds": math.inf},
    {"health_age_seconds": -1}, {"reach_healthy": "yes"},
    {"remaining_queries": True}, {"remaining_queries": -1},
]


def test_budget_cap():
    assert run(remaining_queries=1).max_queries == 1
    assert run(remaining_queries=100).max_queries == 2


class ReachTests(unittest.TestCase):
    def test_routes(self):
        for changes, route in ROUTES:
            with self.subTest(changes=changes):
                check_routing(changes, route)

    def test_invalid(self):
        for changes in INVALID:
            with self.subTest(changes=changes):
                with self.assertRaises(ValueError):
                    run(**changes)

    def test_caps(self):
        test_budget_cap()

if __name__ == "__main__":
    unittest.main()


class ReachSessionTests(unittest.TestCase):
    def test_caps_and_deduplicates(self):
        from source_failover import ReachReadSession
        calls = []
        def reader(url):
            calls.append(url)
            return "a" * 5000
        session = ReachReadSession(run(), reader)
        evidence = session.read("https://example.com/a")
        self.assertEqual(len(evidence["excerpt"]), 1200)
        self.assertTrue(evidence["truncated"])
        self.assertEqual(evidence["classification"], "CLAIM")
        self.assertEqual(session.read("https://example.com/a")["status"], "duplicate")
        session.read("https://example.com/b")
        with self.assertRaises(ValueError):
            session.read("https://example.com/c")
        self.assertEqual(len(calls), 2)

    def test_failed_reads_consume_budget(self):
        from source_failover import ReachReadSession
        def broken(url):
            raise TimeoutError()
        session = ReachReadSession(run(remaining_queries=1), broken)
        with self.assertRaises(TimeoutError):
            session.read("https://example.com/a")
        self.assertEqual(session.remaining, 0)

    def test_private_routing_cannot_execute(self):
        from source_failover import ReachReadSession
        with self.assertRaises(ValueError):
            ReachReadSession(run(sensitivity="restricted"), lambda url: "x")
