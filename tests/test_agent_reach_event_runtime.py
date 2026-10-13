import asyncio
import json
import unittest
from dataclasses import asdict
from types import SimpleNamespace
from unittest.mock import patch

from agent import process_event
from source_failover import ReachAcquisitionError, agent_reach_preflight
from state import EventRecord


class FakeStore:
    def __init__(self):
        self.status = None
    def begin(self, event):
        return 'new'
    def set_status(self, event_id, status):
        self.status = status


class EventRuntimeTests(unittest.TestCase):
    def preflight(self):
        return dict(gate='SAFE', project_id='hydrostatic_tester', external_action_authorized=False,
                    acquisition=asdict(agent_reach_preflight(
                        project_id='hydrostatic_tester', lane_id='discovery',
                        needs_external_evidence=True, sensitivity='public',
                        native_available=False, cache_fresh=False, reach_healthy=True,
                        health_age_seconds=5, remaining_queries=2)))

    def event(self):
        return EventRecord('reach-test', 'hydrostatic_tester', 'research',
                           {'_nexus_preflight': {'acquisition': {'urls': ['https://github.com/']}}})

    def test_evidence_enters_model_envelope(self):
        store = FakeStore()
        evidence = [{'classification': 'CLAIM', 'excerpt': 'public fixture'}]
        with patch('agent.preflight_event', return_value=self.preflight()), \
             patch('agent.collect_reach_evidence', return_value=evidence) as collector, \
             patch('agent.ResponsesClient') as client:
            client.return_value.run.return_value = SimpleNamespace(output_text='ok')
            result = asyncio.run(process_event(store, self.event()))
        self.assertEqual(result, 'ok')
        envelope = json.loads(client.return_value.run.call_args.kwargs['input_text'])
        self.assertEqual(envelope['acquired_evidence'], evidence)
        self.assertEqual(store.status, 'analyzed')
        collector.assert_called_once()

    def test_read_failure_blocks_model(self):
        store = FakeStore()
        with patch('agent.preflight_event', return_value=self.preflight()), \
             patch('agent.collect_reach_evidence', side_effect=ReachAcquisitionError('reach_read_failed')), \
             patch('agent.ResponsesClient') as client:
            result = json.loads(asyncio.run(process_event(store, self.event())))
        self.assertEqual(result['status'], 'blocked_acquisition')
        self.assertEqual(store.status, 'blocked_acquisition')
        client.assert_not_called()


    def test_unknown_project_never_fetches(self):
        store = FakeStore()
        event = EventRecord('unknown', 'not_registered', 'research', {})
        with patch('agent.preflight_event', return_value=self.preflight()), \
             patch('agent.collect_reach_evidence') as collector, \
             patch('agent.ResponsesClient') as client:
            result = json.loads(asyncio.run(process_event(store, event)))
        self.assertEqual(result['status'], 'blocked_project')
        collector.assert_not_called()
        client.assert_not_called()

    def test_forbidden_project_action_never_fetches(self):
        store = FakeStore()
        event = self.event()
        event.payload['requested_action'] = 'outreach_boyu'
        with patch('agent.preflight_event', return_value=self.preflight()), \
             patch('agent.collect_reach_evidence') as collector, \
             patch('agent.ResponsesClient') as client:
            result = json.loads(asyncio.run(process_event(store, event)))
        self.assertEqual(result['status'], 'blocked_project')
        collector.assert_not_called()
        client.assert_not_called()
