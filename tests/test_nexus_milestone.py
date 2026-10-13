import pytest
from nexus_milestone import Milestone
def test_positive_milestone_requires_evidence():
 with pytest.raises(ValueError,match="positive_status_requires_evidence"):Milestone("TESTED","qa","green").to_json()
def test_next_does_not_fake_completion():
 assert '"status": "NEXT"' in Milestone("NEXT","trade","query official trade data").to_json()
def test_tested_with_evidence_serializes():
 assert "ci:956" in Milestone("TESTED","qa","CI passed",("ci:956",)).to_json()
