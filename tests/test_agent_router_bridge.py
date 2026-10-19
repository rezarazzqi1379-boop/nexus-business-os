import unittest
from unittest.mock import patch
from nexus_agent_router_bridge import run_planned_synthetic
from project_control_plane import CoordinationPlan, AgentAssignment

class BridgeTests(unittest.TestCase):
    def test_unqualified_agent_fails_closed(self):
        with self.assertRaises(PermissionError):
            run_planned_synthetic('task', 'PRJ-NEXUS-SANDBOX', 'check',
                                  problem_tags=('nonexistent_problem_tag_734982',),
                                  required_capabilities=('nonexistent_capability_734982',))

    def test_blocked_plan_fails_closed(self):
        plan = CoordinationPlan('test', (), {}, None, (), (('task', 'blocked'),))
        with patch('nexus_agent_router_bridge.build_coordination_plan', return_value=plan):
            with self.assertRaises(PermissionError):
                run_planned_synthetic('task', 'PRJ-NEXUS-SANDBOX', 'check',
                                      problem_tags=('research',), required_capabilities=('search',))

    def test_identity_validation(self):
        with self.assertRaises(ValueError):
            run_planned_synthetic('', 'P', 'check', problem_tags=('research',),
                                  required_capabilities=('search',))

if __name__ == '__main__':
    unittest.main()
