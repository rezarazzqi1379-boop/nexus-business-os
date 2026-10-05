from agent_scout_registry import *

def test_discovery_does_not_equal_activation():
 x=AgentCandidate("A","https://example.invalid/repo","research","reduce discovery blind spots")
 assert not can_activate(x)

def test_sandbox_requires_rollback_and_acceptance_test():
 x=AgentCandidate("A","repo","research","job",state="SANDBOXED",license="MIT")
 assert "sandbox_requires_rollback_and_acceptance_test" in x.validate()

def test_active_candidate_must_have_governance_fields():
 x=AgentCandidate("A","repo","research","job",state="ACTIVE",license="MIT",maintenance="ACTIVE",network_credentials="NONE",rollback="remove adapter",acceptance_test="held-out benchmark")
 assert can_activate(x)
