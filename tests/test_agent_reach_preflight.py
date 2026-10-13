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

class ReachCollectorTests(unittest.TestCase):
    def setUp(self):
        from dataclasses import asdict
        self.preflight = dict(gate='SAFE', project_id='PRJ-HYD-01',
                              acquisition=asdict(run()))
        self.control = dict(urls=['https://github.com/Panniantong/Agent-Reach'])

    def test_real_collector_enforces_caps(self):
        from source_failover import collect_reach_evidence
        result = collect_reach_evidence(self.preflight, self.control,
                                        reader=lambda url: 'x' * 5000, enabled=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0]['excerpt']), 1200)
        self.assertEqual(result[0]['project_id'], 'PRJ-HYD-01')

    def test_batch_validated_before_any_read(self):
        from source_failover import collect_reach_evidence, ReachAcquisitionError
        calls = []
        self.control['urls'].append('https://localhost/secret')
        with self.assertRaises(ReachAcquisitionError):
            collect_reach_evidence(self.preflight, self.control,
                                   reader=lambda url: calls.append(url), enabled=True)
        self.assertEqual(calls, [])

    def test_disabled_and_review_do_not_call_reader(self):
        from source_failover import collect_reach_evidence, ReachAcquisitionError
        for enabled, gate in ((False, 'SAFE'), (True, 'REVIEW'), (True, 'BLOCK')):
            calls = []
            self.preflight['gate'] = gate
            with self.assertRaises(ReachAcquisitionError):
                collect_reach_evidence(self.preflight, self.control,
                                       reader=lambda url: calls.append(url), enabled=enabled)
            self.assertEqual(calls, [])

    def test_backend_errors_are_sanitized(self):
        from source_failover import collect_reach_evidence, ReachAcquisitionError
        def reader(url):
            raise RuntimeError('sensitive backend body')
        with self.assertRaisesRegex(ReachAcquisitionError, '^reach_read_failed$'):
            collect_reach_evidence(self.preflight, self.control, reader=reader, enabled=True)

    def test_non_reach_route_makes_no_calls(self):
        from source_failover import collect_reach_evidence
        self.preflight['acquisition']['route'] = 'native'
        self.assertEqual(collect_reach_evidence(self.preflight, {}, enabled=False), [])
