import unittest
from nexus_agent_router_pilot import WorkRequest, WorkerResult, demo, run_parallel, synthetic_worker

class AgentRouterPilotTests(unittest.TestCase):
    def test_three_workers(self):
        r = demo()
        self.assertEqual(r['status'], 'COMPLETE')
        self.assertEqual(set(r['results']), {'research', 'reconciliation', 'qa'})

    def test_reject_consequential_action(self):
        with self.assertRaises(PermissionError):
            run_parallel(WorkRequest('P', 'T', 'send', action_kind='SEND_EMAIL'), {'qa': synthetic_worker('qa')})

    def test_reject_approval_required(self):
        with self.assertRaises(PermissionError):
            run_parallel(WorkRequest('P', 'T', 'send', approval_required=True), {'qa': synthetic_worker('qa')})

    def test_project_isolation(self):
        def wrong(req):
            return WorkerResult('qa', 'OTHER', req.task_id, 'COMPLETE', (), 'wrong')
        r = run_parallel(WorkRequest('P', 'T', 'test'), {'qa': wrong})
        self.assertEqual(r['status'], 'REVIEW')
        self.assertEqual(r['results']['qa'].status, 'FAILED')

    def test_empty_workers_rejected(self):
        with self.assertRaises(ValueError):
            run_parallel(WorkRequest('P', 'T', 'test'), {})

    def test_ten_repetitions(self):
        for _ in range(10):
            self.assertEqual(demo()['status'], 'COMPLETE')

if __name__ == '__main__':
    unittest.main()
